import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDataStore } from '../store/dataStore';
import { brands, projects as projectsApi } from '../services/api';
import { ArrowLeft, Plus, Calendar, Sparkles, Loader2, Settings, Trash2, Mic } from 'lucide-react';

export default function BrandDetail() {
  const { brandId } = useParams();
  const navigate = useNavigate();
  const { projects, fetchProjects, isLoading } = useDataStore();
  const [brand, setBrand] = useState(null);

  useEffect(function() {
    brands.get(brandId).then(function(res) { setBrand(res.data); });
    fetchProjects(brandId);
  }, [brandId]);

  if (!brand) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="animate-spin" /></div>;

  const handleDeleteProject = async function(e, projectId) {
    e.stopPropagation();
    if (window.confirm('Sei sicuro di voler eliminare questo calendario?')) {
      try {
        await projectsApi.delete(projectId);
        fetchProjects(brandId);
      } catch (err) {
        alert('Errore durante l eliminazione');
      }
    }
  };

  const goToVoiceInterview = function() {
    navigate('/brand/' + brandId + '/voice-interview');
  };

  const goToNewProject = function() {
    navigate('/brand/' + brandId + '/new-project');
  };

  const goToProject = function(projectId) {
    navigate('/project/' + projectId);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button onClick={function() { navigate('/dashboard'); }} className="flex items-center gap-2 text-gray-600 hover:text-[#3DAFA8] mb-2">
            <ArrowLeft size={20} /> Dashboard
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-[#2C3E50]">{brand.name}</h1>
              <p className="text-sm text-gray-500">{brand.sector} - {brand.tone_of_voice}</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Calendar className="text-[#3DAFA8]" /> Calendari Editoriali
          </h2>
          <div className="flex gap-3">
            <button
              onClick={goToVoiceInterview}
              className="flex items-center gap-2 bg-[#E89548] text-white px-5 py-2.5 rounded-lg hover:bg-[#d4823c] transition-colors"
              title="Crea calendario con intervista AI"
            >
              <Mic size={20} /> Intervista AI
            </button>
            <button
              onClick={goToNewProject}
              className="flex items-center gap-2 bg-[#3DAFA8] text-white px-5 py-2.5 rounded-lg hover:bg-[#2C3E50] transition-colors"
            >
              <Sparkles size={20} /> Wizard Manuale
            </button>
          </div>
        </div>

        {isLoading ? (
          <div className="text-center py-12"><Loader2 className="animate-spin mx-auto" /></div>
        ) : projects.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center">
            <Calendar size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">Nessun calendario</h3>
            <p className="text-gray-500 mb-6">Crea il tuo primo calendario editoriale</p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={goToVoiceInterview}
                className="inline-flex items-center gap-2 bg-[#E89548] text-white px-6 py-3 rounded-lg hover:bg-[#d4823c]"
              >
                <Mic size={20} /> Intervista AI
              </button>
              <button
                onClick={goToNewProject}
                className="inline-flex items-center gap-2 bg-[#3DAFA8] text-white px-6 py-3 rounded-lg hover:bg-[#2C3E50]"
              >
                <Plus size={20} /> Wizard Manuale
              </button>
            </div>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map(function(project) {
              return (
                <div
                  key={project.id}
                  onClick={function() { goToProject(project.id); }}
                  className="bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow cursor-pointer relative group"
                >
                  <button
                    onClick={function(e) { handleDeleteProject(e, project.id); }}
                    className="absolute top-3 right-3 p-2 text-gray-400 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Elimina calendario"
                  >
                    <Trash2 size={18} />
                  </button>
                  <h3 className="font-semibold text-[#2C3E50] mb-2">{project.name}</h3>
                  <p className="text-sm text-gray-500 mb-4">{project.description || 'Nessuna descrizione'}</p>
                  <div className="flex items-center justify-between text-xs text-gray-400">
                    <span>{project.posts_count || 0} post</span>
                    <span>{new Date(project.created_at).toLocaleDateString('it-IT')}</span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </main>
    </div>
  );
}
