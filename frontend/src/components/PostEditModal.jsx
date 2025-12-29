import { useState, useEffect } from 'react';
import { format, parseISO } from 'date-fns';
import { it } from 'date-fns/locale';

const platformColors = {
  linkedin: 'bg-[#0077b5]',
  instagram: 'bg-gradient-to-r from-[#f09433] via-[#dc2743] to-[#bc1888]',
  facebook: 'bg-[#1877f2]',
  google: 'bg-[#34a853]',
  blog: 'bg-[#9b59b6]',
};

const platformIcons = {
  linkedin: '💼',
  instagram: '📸',
  facebook: '👥',
  google: '📍',
  blog: '📝',
};

const API_URL = import.meta.env.VITE_API_URL || '';

export default function PostEditModal({ post, isOpen, onClose, onSave }) {
  const [editedPost, setEditedPost] = useState(null);
  const [isSaving, setIsSaving] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isGeneratingImage, setIsGeneratingImage] = useState(false);
  const [activeTab, setActiveTab] = useState('content');
  const [message, setMessage] = useState(null);

  useEffect(() => {
    if (post) {
      setEditedPost({
        ...post,
        hashtagsText: Array.isArray(post.hashtags) 
          ? post.hashtags.map(h => h.startsWith('#') ? h.slice(1) : h).join(', ') 
          : ''
      });
      setActiveTab('content');
      setMessage(null);
    }
  }, [post]);

  if (!isOpen || !editedPost) return null;

  const handleChange = (field, value) => {
    setEditedPost(prev => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    setIsSaving(true);
    setMessage(null);
    try {
      const hashtagsArray = editedPost.hashtagsText
        .split(',')
        .map(h => h.trim().replace(/^#/, ''))
        .filter(h => h.length > 0);

      const response = await fetch(`${API_URL}/api/posts/${editedPost.id}`, {
        method: 'PATCH',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          content: editedPost.content,
          hashtags: hashtagsArray,
          scheduled_time: editedPost.scheduled_time,
          scheduled_date: editedPost.scheduled_date,
          visual_suggestion: editedPost.visual_suggestion,
          cta: editedPost.cta,
          pillar: editedPost.pillar
        })
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Errore nel salvataggio');
      }
      
      const updated = await response.json();
      setMessage({ type: 'success', text: '✅ Post salvato con successo!' });
      
      setTimeout(() => {
        if (onSave) onSave(updated);
        onClose();
      }, 1000);
    } catch (error) {
      setMessage({ type: 'error', text: '❌ ' + error.message });
    } finally {
      setIsSaving(false);
    }
  };

  const handleRegenerate = async () => {
    setIsRegenerating(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_URL}/api/posts/${editedPost.id}/regenerate`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Errore nella rigenerazione');
      }
      
      const regenerated = await response.json();
      setEditedPost({
        ...regenerated,
        hashtagsText: Array.isArray(regenerated.hashtags) 
          ? regenerated.hashtags.map(h => h.startsWith('#') ? h.slice(1) : h).join(', ') 
          : ''
      });
      setMessage({ type: 'success', text: '🔄 Post rigenerato con AI!' });
    } catch (error) {
      setMessage({ type: 'error', text: '❌ ' + error.message });
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleGenerateImage = async () => {
    setIsGeneratingImage(true);
    setMessage(null);
    try {
      const response = await fetch(`${API_URL}/api/posts/${editedPost.id}/generate-image`, {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Errore nella generazione immagine');
      }
      
      const result = await response.json();
      setEditedPost(prev => ({ ...prev, image_url: result.image_url }));
      setMessage({ type: 'success', text: '🎨 Immagine generata con successo!' });
    } catch (error) {
      setMessage({ type: 'error', text: '❌ ' + error.message });
    } finally {
      setIsGeneratingImage(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setMessage({ type: 'success', text: '📋 Copiato negli appunti!' });
    setTimeout(() => setMessage(null), 2000);
  };

  return (
    <div className="fixed inset-0 bg-black/70 z-50 flex items-center justify-center p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col shadow-2xl" onClick={e => e.stopPropagation()}>
        
        {/* Header */}
        <div className="bg-gradient-to-r from-slate-700 to-slate-800 text-white p-5">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-xl font-bold">
                ✏️ Modifica Post - {format(parseISO(editedPost.scheduled_date), "EEEE d MMMM yyyy", { locale: it })}
              </h2>
              <div className="flex items-center gap-3 mt-2">
                <span className={`${platformColors[editedPost.platform]} text-white px-3 py-1 rounded text-sm font-semibold capitalize`}>
                  {platformIcons[editedPost.platform]} {editedPost.platform}
                </span>
                <span className="bg-white/20 px-3 py-1 rounded text-sm">{editedPost.scheduled_time}</span>
                <span className="bg-orange-500 px-3 py-1 rounded text-sm font-medium">{editedPost.pillar}</span>
              </div>
            </div>
            <button onClick={onClose} className="text-white/70 hover:text-white text-3xl leading-none">×</button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b bg-gray-50">
          {['content', 'visual', 'settings'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex-1 py-3 px-4 font-medium transition-colors ${
                activeTab === tab 
                  ? 'bg-white text-teal-600 border-b-2 border-teal-500' 
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'content' && '📝 Contenuto'}
              {tab === 'visual' && '🎨 Visual & Immagine'}
              {tab === 'settings' && '⚙️ Impostazioni'}
            </button>
          ))}
        </div>

        {/* Message */}
        {message && (
          <div className={`mx-5 mt-4 p-3 rounded-lg font-medium ${
            message.type === 'success' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          }`}>
            {message.text}
          </div>
        )}

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5">
          {activeTab === 'content' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Contenuto del Post</label>
                <textarea
                  value={editedPost.content || ''}
                  onChange={(e) => handleChange('content', e.target.value)}
                  className="w-full h-52 p-4 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none resize-none text-gray-800 leading-relaxed"
                  placeholder="Scrivi il contenuto del post..."
                />
                <div className="flex justify-between mt-2 text-sm text-gray-500">
                  <span>{editedPost.content?.length || 0} caratteri</span>
                  <button onClick={() => copyToClipboard(editedPost.content)} className="text-teal-600 hover:text-teal-700 font-medium">
                    📋 Copia contenuto
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Hashtag (separati da virgola)</label>
                <input
                  type="text"
                  value={editedPost.hashtagsText || ''}
                  onChange={(e) => handleChange('hashtagsText', e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none"
                  placeholder="AI, Innovazione, Noscite, UmanesimoDigitale"
                />
                <button 
                  onClick={() => copyToClipboard(editedPost.hashtagsText.split(',').map(h => `#${h.trim()}`).join(' '))}
                  className="mt-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                >
                  🏷️ Copia come #hashtag
                </button>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Call to Action</label>
                <input
                  type="text"
                  value={editedPost.cta || ''}
                  onChange={(e) => handleChange('cta', e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none"
                  placeholder="Scopri di più sul nostro sito..."
                />
              </div>
            </div>
          )}

          {activeTab === 'visual' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Suggerimento Visual / Prompt per AI</label>
                <textarea
                  value={editedPost.visual_suggestion || ''}
                  onChange={(e) => handleChange('visual_suggestion', e.target.value)}
                  className="w-full h-32 p-4 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none resize-none"
                  placeholder="Descrivi il visual per questo post... Es: 'Grafica minimalista con icona di AI su sfondo teal, stile Noscite'"
                />
              </div>

              {editedPost.image_url && (
                <div className="bg-gray-50 rounded-xl p-4">
                  <label className="block text-sm font-semibold text-gray-700 mb-3">Immagine Generata</label>
                  <img 
                    src={editedPost.image_url} 
                    alt="Generated" 
                    className="w-full max-w-lg rounded-xl shadow-lg mx-auto" 
                  />
                  <div className="mt-3 text-center">
                    <a 
                      href={editedPost.image_url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="text-teal-600 hover:text-teal-700 text-sm font-medium"
                    >
                      🔗 Apri immagine in nuova tab
                    </a>
                  </div>
                </div>
              )}

              <button
                onClick={handleGenerateImage}
                disabled={isGeneratingImage || !editedPost.visual_suggestion}
                className={`w-full py-3 px-4 rounded-xl font-semibold flex items-center justify-center gap-2 transition-all ${
                  isGeneratingImage || !editedPost.visual_suggestion
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:from-purple-600 hover:to-pink-600 shadow-lg hover:shadow-xl'
                }`}
              >
                {isGeneratingImage ? (
                  <>
                    <span className="animate-spin">⏳</span> Generazione immagine in corso...
                  </>
                ) : (
                  <>🎨 Genera Immagine con DALL-E</>
                )}
              </button>
              {!editedPost.visual_suggestion && (
                <p className="text-sm text-gray-500 text-center">💡 Inserisci un suggerimento visual per abilitare la generazione immagine</p>
              )}
            </div>
          )}

          {activeTab === 'settings' && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Data Pubblicazione</label>
                  <input
                    type="date"
                    value={editedPost.scheduled_date || ''}
                    onChange={(e) => handleChange('scheduled_date', e.target.value)}
                    className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-sm font-semibold text-gray-700 mb-2">Orario</label>
                  <input
                    type="time"
                    value={editedPost.scheduled_time?.slice(0,5) || '09:00'}
                    onChange={(e) => handleChange('scheduled_time', e.target.value)}
                    className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">Pillar / Tema</label>
                <input
                  type="text"
                  value={editedPost.pillar || ''}
                  onChange={(e) => handleChange('pillar', e.target.value)}
                  className="w-full p-3 border-2 border-gray-200 rounded-xl focus:border-teal-500 focus:outline-none"
                  placeholder="Umanesimo Digitale"
                />
              </div>

              <div className="bg-gray-50 rounded-xl p-4">
                <h4 className="font-semibold text-gray-700 mb-3">📊 Info Post</h4>
                <div className="text-sm text-gray-600 space-y-2">
                  <p><strong>ID:</strong> {editedPost.id}</p>
                  <p><strong>Piattaforma:</strong> <span className="capitalize">{editedPost.platform}</span></p>
                  <p><strong>Formato:</strong> {editedPost.format || 'standard'}</p>
                  <p><strong>Progetto ID:</strong> {editedPost.project_id}</p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 p-5 flex gap-3 flex-wrap">
          <button
            onClick={handleRegenerate}
            disabled={isRegenerating}
            className={`px-5 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              isRegenerating 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-amber-500 to-orange-500 text-white hover:from-amber-600 hover:to-orange-600 shadow-md hover:shadow-lg'
            }`}
          >
            {isRegenerating ? (
              <><span className="animate-spin">⏳</span> Rigenerazione...</>
            ) : (
              <>🔄 Rigenera con AI</>
            )}
          </button>
          
          <div className="flex-1"></div>
          
          <button
            onClick={onClose}
            className="px-5 py-2.5 border-2 border-gray-300 text-gray-600 rounded-xl font-semibold hover:bg-gray-100 transition-all"
          >
            Annulla
          </button>
          
          <button
            onClick={handleSave}
            disabled={isSaving}
            className={`px-6 py-2.5 rounded-xl font-semibold flex items-center gap-2 transition-all ${
              isSaving 
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-teal-500 to-teal-600 text-white hover:from-teal-600 hover:to-teal-700 shadow-md hover:shadow-lg'
            }`}
          >
            {isSaving ? (
              <><span className="animate-spin">⏳</span> Salvataggio...</>
            ) : (
              <>💾 Salva Modifiche</>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
