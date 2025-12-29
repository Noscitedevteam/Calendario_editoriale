from sqlalchemy.orm import Session
from app.models.project import Project, ProjectStatus
from app.models.brand import Brand, BrandDocument
from app.models.post import Post
from app.services.claude_service import generate_editorial_plan
from app.services.perplexity_service import search_trends, fetch_url_content
from datetime import datetime

async def generate_calendar(project_id: int, db: Session):
    """Genera calendario completo per un progetto"""
    
    # Carica progetto e brand
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise ValueError("Project not found")
    
    brand = db.query(Brand).filter(Brand.id == project.brand_id).first()
    if not brand:
        raise ValueError("Brand not found")
    
    # Aggiorna stato
    project.status = ProjectStatus.generating
    db.commit()
    
    try:
        # Raccogli contenuto documenti brand
        reference_content = ""
        documents = db.query(BrandDocument).filter(BrandDocument.brand_id == brand.id).all()
        for doc in documents:
            if doc.extracted_content:
                reference_content += f"\n--- {doc.filename} ---\n{doc.extracted_content}\n"
        
        # Fetch contenuto da URL se presenti
        urls_content = ""
        if project.reference_urls:
            for url in project.reference_urls[:5]:  # Max 5 URL
                try:
                    content = await fetch_url_content(url)
                    if content:
                        urls_content += f"\n--- {url} ---\n{content[:2000]}\n"
                except:
                    pass
        
        # Ricerca trend del settore
        trends = ""
        if brand.sector:
            try:
                trends = await search_trends(brand.sector, brand.name)
                reference_content += f"\n--- TREND DI SETTORE ---\n{trends}\n"
            except:
                pass
        
        # Genera piano con Claude
        posts_data = generate_editorial_plan(
            brand_name=brand.name,
            brand_sector=brand.sector or "",
            tone_of_voice=brand.tone_of_voice or "professionale",
            brand_values=brand.brand_values or "",
            start_date=project.start_date.isoformat(),
            end_date=project.end_date.isoformat(),
            platforms=project.platforms,
            posts_per_week=project.posts_per_week,
            brief=project.brief or "",
            themes=project.themes or project.content_pillars,
            reference_content=reference_content,
            urls_content=urls_content
        )
        
        # Elimina post esistenti
        db.query(Post).filter(Post.project_id == project_id).delete()
        
        # Salva nuovi post
        for post_data in posts_data:
            post = Post(
                project_id=project_id,
                platform=post_data.get('platform', 'linkedin'),
                scheduled_date=datetime.strptime(post_data.get('scheduled_date', project.start_date.isoformat()), '%Y-%m-%d').date(),
                scheduled_time=post_data.get('scheduled_time', '09:00'),
                content=post_data.get('content', ''),
                hashtags=post_data.get('hashtags', []),
                pillar=post_data.get('pillar', ''),
                post_type=post_data.get('post_type', 'educational'),
                visual_suggestion=post_data.get('visual_suggestion', ''),
                cta=post_data.get('cta', '')
            )
            db.add(post)
        
        project.status = ProjectStatus.review
        db.commit()
        
        return {"success": True, "posts_count": len(posts_data)}
        
    except Exception as e:
        project.status = ProjectStatus.draft
        db.commit()
        print(f"Error generating calendar: {e}")
        raise
