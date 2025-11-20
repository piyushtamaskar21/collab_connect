import { useState } from 'react';
import { ResumeUploader } from './components/ResumeUploader';
import { RecommendationsGrid } from './components/RecommendationsGrid';
import { EmployeeProfileModal, type EmployeeProfile } from './components/EmployeeProfileModal';
import type { Employee } from './components/EmployeeCard';
import { Users, Sparkles } from 'lucide-react';

function App() {
  const [recommendations, setRecommendations] = useState<Employee[]>([]);
  const [isFetching, setIsFetching] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedEmployee, setSelectedEmployee] = useState<EmployeeProfile | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const handleReadMore = (employee: Employee) => {
    setSelectedEmployee(employee as EmployeeProfile);
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setTimeout(() => setSelectedEmployee(null), 300); // Delay to allow animation
  };

  const handleTextExtracted = async (text: string) => {
    setIsFetching(true);
    setError(null);

    try {
      // Call the backend API
      const response = await fetch('http://localhost:8000/api/recommend', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ resumeText: text }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch recommendations');
      }

      const data = await response.json();
      setRecommendations(data.recommendations);
    } catch (err) {
      console.error(err);
      setError('Failed to get recommendations from the server. Is the backend running?');
    } finally {
      setIsFetching(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f5] pb-20">
      {/* Header */}
      <header className="bg-black sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center space-x-3">
            <div className="bg-white p-1.5 rounded">
              <Users className="w-5 h-5 text-black" />
            </div>
            <h1 className="text-xl font-semibold text-white">CollabConnect</h1>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
        <div className="text-center mb-16 max-w-3xl mx-auto">
          <h2 className="text-4xl font-light text-black sm:text-5xl mb-6">
            Learn more about your recommended <span className="font-normal">collaborators</span>
          </h2>
          <p className="text-base text-gray-700 leading-relaxed">
            Upload your resume or project description to discover colleagues with complementary skills and shared interests.
          </p>
        </div>

        <ResumeUploader onTextExtracted={handleTextExtracted} />

        {isFetching && (
          <div className="mt-12 text-center">
            <div className="inline-flex items-center px-4 py-2 font-semibold leading-6 text-blue-600 transition ease-in-out duration-150 cursor-not-allowed">
              <Sparkles className="animate-spin -ml-1 mr-3 h-5 w-5 text-blue-600" />
              Analyzing profile and finding matches...
            </div>
          </div>
        )}

        {error && (
          <div className="mt-8 max-w-2xl mx-auto p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-center">
            {error}
          </div>
        )}

        {!isFetching && <RecommendationsGrid recommendations={recommendations} onReadMore={handleReadMore} />}
      </main>

      {/* Employee Profile Modal */}
      {selectedEmployee && (
        <EmployeeProfileModal
          employee={selectedEmployee}
          isOpen={isModalOpen}
          onClose={closeModal}
        />
      )}
    </div>
  );
}

export default App;
