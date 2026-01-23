from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional
import httpx
import logging

from app.core.database import get_db
from app.core.config import settings
from app.core.auth import get_current_user
from app.models.user import User
from app.models.brand import Brand
from app.models.social_connection import SocialConnection, PostPublication, SocialMetric

logger = logging.getLogger(__name__)
router = APIRouter()


# === SCHEMAS ===
from pydantic import BaseModel
from typing import List, Dict, Any

class MetricSummary(BaseModel):
    platform: str
    impressions: int = 0
    reach: int = 0
    engagement: int = 0
    likes: int = 0
    comments: int = 0
    shares: int = 0
    followers_count: Optional[int] = None

class BrandStatsResponse(BaseModel):
    brand_id: int
    brand_name: str
    period_start: datetime
    period_end: datetime
    platforms: List[MetricSummary]
    total_posts: int
    published_posts: int
    engagement_rate: float


# === ENDPOINTS ===

@router.get("/brand/{brand_id}")
async def get_brand_stats(
    brand_id: int,
    days: int = 30,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Statistiche aggregate per brand"""
    
    # Verifica accesso brand
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    period_start = datetime.utcnow() - timedelta(days=days)
    period_end = datetime.utcnow()
    
    # Connessioni social del brand
    connections = db.query(SocialConnection).filter(
        SocialConnection.brand_id == brand_id,
        SocialConnection.is_active == True
    ).all()
    
    platforms = []
    for conn in connections:
        # Metriche aggregate per connessione
        metrics = db.query(
            func.sum(SocialMetric.impressions).label('impressions'),
            func.sum(SocialMetric.reach).label('reach'),
            func.sum(SocialMetric.engagement).label('engagement'),
            func.sum(SocialMetric.likes).label('likes'),
            func.sum(SocialMetric.comments).label('comments'),
            func.sum(SocialMetric.shares).label('shares'),
            func.max(SocialMetric.followers_count).label('followers')
        ).filter(
            SocialMetric.social_connection_id == conn.id,
            SocialMetric.metric_date >= period_start
        ).first()
        
        platforms.append({
            "platform": conn.platform,
            "account_name": conn.external_account_name,
            "impressions": metrics.impressions or 0,
            "reach": metrics.reach or 0,
            "engagement": metrics.engagement or 0,
            "likes": metrics.likes or 0,
            "comments": metrics.comments or 0,
            "shares": metrics.shares or 0,
            "followers_count": metrics.followers
        })
    
    # Conteggio post
    total_posts = db.query(PostPublication).join(SocialConnection).filter(
        SocialConnection.brand_id == brand_id
    ).count()
    
    published_posts = db.query(PostPublication).join(SocialConnection).filter(
        SocialConnection.brand_id == brand_id,
        PostPublication.status == "published"
    ).count()
    
    # Calcolo engagement rate
    total_engagement = sum(p.get("engagement", 0) for p in platforms)
    total_reach = sum(p.get("reach", 0) for p in platforms)
    engagement_rate = (total_engagement / total_reach * 100) if total_reach > 0 else 0
    
    return {
        "brand_id": brand_id,
        "brand_name": brand.name,
        "period_start": period_start,
        "period_end": period_end,
        "platforms": platforms,
        "total_posts": total_posts,
        "published_posts": published_posts,
        "engagement_rate": round(engagement_rate, 2)
    }


@router.post("/fetch/{brand_id}")
async def fetch_stats_from_platforms(
    brand_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Recupera statistiche aggiornate dalle piattaforme social"""
    
    # Verifica accesso brand
    brand = db.query(Brand).filter(
        Brand.id == brand_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not brand:
        raise HTTPException(status_code=404, detail="Brand non trovato")
    
    connections = db.query(SocialConnection).filter(
        SocialConnection.brand_id == brand_id,
        SocialConnection.is_active == True
    ).all()
    
    results = []
    
    for conn in connections:
        try:
            if conn.platform == "facebook":
                stats = await fetch_facebook_stats(conn, db)
            elif conn.platform == "instagram":
                stats = await fetch_instagram_stats(conn, db)
            elif conn.platform == "linkedin":
                stats = await fetch_linkedin_stats(conn, db)
            else:
                stats = {"status": "unsupported"}
            
            results.append({
                "platform": conn.platform,
                "account": conn.external_account_name,
                "status": "success",
                "metrics_fetched": stats.get("count", 0)
            })
        except Exception as e:
            logger.error(f"Errore fetch stats {conn.platform}: {e}")
            results.append({
                "platform": conn.platform,
                "account": conn.external_account_name,
                "status": "error",
                "error": str(e)
            })
    
    return {"brand_id": brand_id, "results": results}


# === FETCH FUNCTIONS ===

async def fetch_facebook_stats(conn: SocialConnection, db: Session) -> dict:
    """Recupera statistiche da Facebook Graph API"""
    
    async with httpx.AsyncClient() as client:
        # Insights della pagina
        response = await client.get(
            f"https://graph.facebook.com/v18.0/{conn.external_account_id}/insights",
            params={
                "access_token": conn.access_token,
                "metric": "page_views_total,page_post_engagements",
                "period": "day",
                
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Facebook API error: {response.text}")
        
        data = response.json()
        count = 0
        
        for metric_data in data.get("data", []):
            metric_name = metric_data.get("name")
            for value in metric_data.get("values", []):
                metric = SocialMetric(
                    social_connection_id=conn.id,
                    metric_date=datetime.fromisoformat(value["end_time"].replace("Z", "+00:00")),
                    metric_type="daily",
                    raw_data={metric_name: value["value"]}
                )
                
                if metric_name == "page_impressions":
                    metric.impressions = value["value"]
                elif metric_name == "page_engaged_users":
                    metric.engagement = value["value"]
                elif metric_name == "page_fans":
                    metric.followers_count = value["value"]
                
                db.add(metric)
                count += 1
        
        db.commit()
        return {"count": count}


async def fetch_instagram_stats(conn: SocialConnection, db: Session) -> dict:
    """Recupera statistiche da Instagram Graph API"""
    
    async with httpx.AsyncClient() as client:
        # Insights dell'account business
        response = await client.get(
            f"https://graph.facebook.com/v18.0/{conn.external_account_id}/insights",
            params={
                "access_token": conn.access_token,
                "metric": "reach,profile_views,accounts_engaged",
                "period": "day",
                "metric_type": "total_value"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"Instagram API error: {response.text}")
        
        data = response.json()
        
        metric = SocialMetric(
            social_connection_id=conn.id,
            metric_date=datetime.utcnow(),
            metric_type="daily",
            raw_data=data
        )
        
        for metric_data in data.get("data", []):
            name = metric_data.get("name")
            value = metric_data.get("total_value", {}).get("value", 0)
            
            if name == "impressions":
                metric.impressions = value
            elif name == "reach":
                metric.reach = value
            elif name == "follower_count":
                metric.followers_count = value
        
        db.add(metric)
        db.commit()
        
        return {"count": 1}


async def fetch_linkedin_stats(conn: SocialConnection, db: Session) -> dict:
    """Recupera statistiche da LinkedIn API"""
    
    # LinkedIn richiede API diverse per profili personali vs pagine aziendali
    async with httpx.AsyncClient() as client:
        # Per ora supportiamo solo profili personali
        if conn.account_type == "profile":
            # LinkedIn non espone facilmente le stats dei post per profili personali
            # Le stats dettagliate richiedono Marketing API con approvazione
            return {"count": 0, "note": "LinkedIn profile stats limited"}
        
        # Per pagine aziendali (richiede Community Management API)
        response = await client.get(
            f"https://api.linkedin.com/v2/organizationalEntityShareStatistics",
            params={
                "q": "organizationalEntity",
                "organizationalEntity": f"urn:li:organization:{conn.external_account_id}"
            },
            headers={
                "Authorization": f"Bearer {conn.access_token}",
                "X-Restli-Protocol-Version": "2.0.0"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"LinkedIn API error: {response.text}")
        
        data = response.json()
        
        metric = SocialMetric(
            social_connection_id=conn.id,
            metric_date=datetime.utcnow(),
            metric_type="daily",
            raw_data=data
        )
        
        elements = data.get("elements", [])
        if elements:
            stats = elements[0].get("totalShareStatistics", {})
            metric.impressions = stats.get("impressionCount", 0)
            metric.engagement = stats.get("engagement", 0)
            metric.clicks = stats.get("clickCount", 0)
            metric.likes = stats.get("likeCount", 0)
            metric.comments = stats.get("commentCount", 0)
            metric.shares = stats.get("shareCount", 0)
        
        db.add(metric)
        db.commit()
        
        return {"count": 1}


@router.get("/post/{publication_id}")
async def get_post_stats(
    publication_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Statistiche di un singolo post pubblicato"""
    
    publication = db.query(PostPublication).join(SocialConnection).join(Brand).filter(
        PostPublication.id == publication_id,
        Brand.organization_id == current_user.organization_id
    ).first()
    
    if not publication:
        raise HTTPException(status_code=404, detail="Pubblicazione non trovata")
    
    metrics = db.query(SocialMetric).filter(
        SocialMetric.post_publication_id == publication_id
    ).order_by(SocialMetric.metric_date.desc()).all()
    
    return {
        "publication_id": publication_id,
        "platform": publication.social_connection.platform,
        "published_at": publication.published_at,
        "external_url": publication.external_post_url,
        "metrics": [
            {
                "date": m.metric_date,
                "impressions": m.impressions,
                "reach": m.reach,
                "likes": m.likes,
                "comments": m.comments,
                "shares": m.shares,
                "engagement": m.engagement
            }
            for m in metrics
        ]
    }
