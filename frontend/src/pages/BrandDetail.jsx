import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDataStore } from '../store/dataStore';
import { brands, projects as projectsApi } from '../services/api';
import { ArrowLeft, Plus, Calendar, Sparkles, Loader2, Settings, Trash2 } from 'lucide-react';

export default function BrandDetail() {
  const { brandId } = useParams();
  const navigate = useNavigate();
  const { projects, fetchProjects, isLoading } = useDataStore();
  const [brand, setBrand] = useState(null);

  useEffect(() => {
    brands.get(brandId).then(res => setBrand(res.data));
    fetchProjects(brandId);
  }, [brandId]);

  if (!brand) return <div className="min-h-screen flex items-center justify-center"><Loader2 className="animate-spin" /></div>;

  const handleDeleteProject = async (e, projectId) => {
    e.stopPropagation();
    if (window.confirm('Sei sicuro di voler eliminare questo calendario?')) {
      try {
        await projectsApi.delete(projectId);
        fetchProjects(brandId);
      } catch (err) {
        alert('Errore durante l\x27eliminazione');
      }
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button onClick={() => navigate('/dashboard')} className="flex items-center gap-2 text-gray-600 hover:text-[#3DAFA8] mb-2">
            <ArrowLeft size={20} /> Dashboard
          </button>
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-2xl font-bold text-[#2C3E50]">{brand.name}</h1>
              <p className="text-sm text-gray-500">{brand.sector} • {brand.tone_of_voice}</p>
            </div>
            <button className="hidden">
              <Settings size={20} />
            </button>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold flex items-center gap-2">
            <Calendar className="text-[#3DAFA8]" /> Calendari Editoriali
          </h2>
          <button
            onClick={() => navigate(`/brand/${brandId}/new-project`)}
            className="flex items-center gap-2 bg-[#3DAFA8] text-white px-5 py-2.5 rounded-lg hover:bg-[#2C3E50] transition-colors"
          >
            <Sparkles size={20} /> Crea Nuovo Calendario
          </button>
        </div>

        {isLoading ? (
          <div className="text-center py-12"><Loader2 className="animate-spin mx-auto" /></div>
        ) : projects.length === 0 ? (
          <div className="bg-white rounded-xl p-12 text-center">
            <Calendar size={48} className="mx-auto text-gray-300 mb-4" />
            <h3 className="text-lg font-medium text-gray-700 mb-2">Nessun calendario</h3>
            <p className="text-gray-500 mb-6">Crea il tuo primo calendario editoriale con il wizard guidato</p>
            <button
              onClick={() => navigate(`/brand/${brandId}/new-project`)}
              className="inline-flex items-center gap-2 bg-[#E89548] text-white px-6 py-3 rounded-lg hover:bg-[#d4823c]"
            >
              <Plus size={20} /> Inizia ora
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => navigate(`/project/${project.id}`)}
                className="bg-white rounded-xl shadow-sm p-6 hover:shadow-md cursor-pointer border-l-4 border-[#E89548] transition-shadow"
              >
                <div className="flex justify-between items-start mb-1"><h3 className="font-semibold text-[#2C3E50]">{project.name}</h3><button onClick={(e) => handleDeleteProject(e, project.id)} className="text-gray-400 hover:text-red-500 p-1"><Trash2 size={16} /></button></div>
                <p className="text-sm text-gray-500 mb-3">
                  {new Date(project.start_date).toLocaleDateString('it-IT')} → {new Date(project.end_date).toLocaleDateString('it-IT')}
                </p>
                <div className="flex gap-2 mb-3">
                  {project.platforms?.map(p => (
                    <span key={p} className="text-xs bg-gray-100 px-2 py-1 rounded capitalize">{p}</span>
                  ))}
                </div>
                <span className={`inline-block text-xs px-3 py-1 rounded-full ${
                  project.status === 'review' ? 'bg-green-100 text-green-700' :
                  project.status === 'generating' ? 'bg-yellow-100 text-yellow-700' :
                  project.status === 'approved' ? 'bg-blue-100 text-blue-700' :
                  'bg-gray-100 text-gray-600'
                }`}>
                  {project.status === 'review' ? '✓ Pronto' : 
                   project.status === 'generating' ? '⏳ In generazione' :
                   project.status === 'approved' ? '✓ Approvato' : 'Bozza'}
                </span>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
