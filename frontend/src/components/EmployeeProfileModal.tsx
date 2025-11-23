import React from 'react';
import { X, Briefcase, MapPin, Mail, Users as UsersIcon, Calendar, Lightbulb, Rocket } from 'lucide-react';
import { SkillChip } from './SkillChip';

interface Project {
    name: string;
    description: string;
    tech: string[];
}

interface ResumeMatch {
    sharedSkills: string[];
    matchingProjects: string[];
    matchingDomains: string[];
    techOverlap: string[];
    matchingSeniority: boolean;
    reasonSummary: string;
}

export interface EmployeeProfile {
    id: string;
    name: string;
    title: string;
    department: string;
    location: string;
    email: string;
    manager: string;
    experienceYears: number;
    professionalSummary: string;
    skills: string[];
    primarySkills: string[];
    secondarySkills: string[];
    tools: string[];
    projects: Project[];
    matchScore: number;
    summary: string;
    avatarUrl: string;
    resumeMatch?: ResumeMatch;
    collaborationSuggestions: string[];
}

interface EmployeeProfileModalProps {
    employee: EmployeeProfile;
    isOpen: boolean;
    onClose: () => void;
}

export const EmployeeProfileModal: React.FC<EmployeeProfileModalProps> = ({ employee, isOpen, onClose }) => {
    if (!isOpen) return null;

    const sharedSkills = employee.resumeMatch?.sharedSkills || [];

    // Handle ESC key
    React.useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    return (
        <div
            className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50 animate-fade-in"
            onClick={onClose}
        >
            <div
                className="bg-white rounded-lg shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden animate-slide-up"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="relative bg-gradient-to-r from-gray-50 to-gray-100 px-8 py-6 border-b border-gray-200">
                    <button
                        onClick={onClose}
                        className="absolute top-4 right-4 p-2 rounded-full hover:bg-gray-200 transition-colors"
                        aria-label="Close"
                    >
                        <X className="w-5 h-5 text-gray-600" />
                    </button>

                    <div className="flex items-start space-x-6">
                        <img
                            src={employee.avatarUrl}
                            alt={employee.name}
                            className="w-20 h-20 rounded-full border-4 border-white shadow-md"
                        />
                        <div className="flex-1">
                            <h2 className="text-2xl font-bold text-gray-900 mb-1">{employee.name}</h2>
                            <div className="flex items-center text-gray-600 mb-2">
                                <Briefcase className="w-4 h-4 mr-2" />
                                <span className="font-medium">{employee.title}</span>
                            </div>
                            <div className="flex flex-wrap gap-3 text-sm text-gray-600">
                                <div className="flex items-center">
                                    <UsersIcon className="w-4 h-4 mr-1" />
                                    {employee.department}
                                </div>
                                <div className="flex items-center">
                                    <MapPin className="w-4 h-4 mr-1" />
                                    {employee.location}
                                </div>
                                <div className="flex items-center">
                                    <Mail className="w-4 h-4 mr-1" />
                                    {employee.email}
                                </div>
                            </div>
                            <div className="mt-2 inline-block bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
                                {(employee.matchScore * 100).toFixed(0)}% Match
                            </div>
                        </div>
                    </div>
                </div>

                {/* Scrollable Content */}
                <div className="overflow-y-auto max-h-[calc(90vh-180px)] px-8 py-6">

                    {/* Match Details (Top Priority) */}
                    <div className="mb-8 space-y-6">
                        {employee.resumeMatch && (
                            <section className="animate-fade-in">
                                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                    <Lightbulb className="w-5 h-5 mr-2 text-yellow-500" />
                                    Why Recommended
                                </h3>
                                <div className="bg-blue-50 rounded-lg p-5 border border-blue-200">
                                    <p className="text-base text-gray-800 leading-relaxed font-medium mb-4">
                                        {employee.resumeMatch.reasonSummary}
                                    </p>
                                    <div className="flex flex-wrap gap-4 text-sm">
                                        {employee.resumeMatch.sharedSkills.length > 0 && (
                                            <div className="bg-white px-3 py-1.5 rounded border border-blue-100 shadow-sm">
                                                <span className="font-semibold text-gray-600 mr-2">Shared Skills:</span>
                                                <span className="text-gray-800">{employee.resumeMatch.sharedSkills.slice(0, 4).join(', ')}</span>
                                            </div>
                                        )}
                                        {employee.resumeMatch.matchingDomains.length > 0 && (
                                            <div className="bg-white px-3 py-1.5 rounded border border-blue-100 shadow-sm">
                                                <span className="font-semibold text-gray-600 mr-2">Domains:</span>
                                                <span className="text-gray-800">{employee.resumeMatch.matchingDomains.join(', ')}</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            </section>
                        )}

                        {employee.collaborationSuggestions.length > 0 && (
                            <section className="animate-fade-in delay-100">
                                <h3 className="text-lg font-semibold text-gray-900 mb-3">Collaboration Ideas</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {employee.collaborationSuggestions.map((suggestion, idx) => (
                                        <div key={idx} className="flex items-start bg-green-50 rounded-lg p-4 border border-green-200 hover:shadow-md transition-shadow">
                                            <span className="text-green-600 mr-3 font-bold text-lg">→</span>
                                            <span className="text-gray-800 text-sm font-medium leading-snug">{suggestion}</span>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        )}
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                        {/* Left Column */}
                        <div className="space-y-8">
                            {/* Experience Section */}
                            <section>
                                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                    <Calendar className="w-5 h-5 mr-2 text-gray-600" />
                                    Experience
                                </h3>
                                <div className="bg-gray-50 rounded-lg p-4 space-y-3">
                                    <div>
                                        <p className="text-sm text-gray-600 mb-1">Years of Experience</p>
                                        <p className="text-base font-semibold text-gray-900">{employee.experienceYears} years</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600 mb-1">Manager</p>
                                        <p className="text-base font-medium text-gray-900">{employee.manager}</p>
                                    </div>
                                    <div>
                                        <p className="text-sm text-gray-600 mb-2">Professional Summary</p>
                                        <p className="text-sm text-gray-700 leading-relaxed">{employee.professionalSummary}</p>
                                    </div>
                                </div>
                            </section>

                            {/* Skills Section */}
                            <section>
                                <h3 className="text-lg font-semibold text-gray-900 mb-3">Skills & Tech Stack</h3>
                                <div className="space-y-4">
                                    <div>
                                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Primary Skills</p>
                                        <div className="flex flex-wrap gap-2">
                                            {employee.primarySkills.map((skill, idx) => (
                                                <SkillChip
                                                    key={idx}
                                                    skill={skill}
                                                    variant={sharedSkills.includes(skill) ? 'shared' : 'normal'}
                                                />
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Secondary Skills</p>
                                        <div className="flex flex-wrap gap-2">
                                            {employee.secondarySkills.map((skill, idx) => (
                                                <SkillChip
                                                    key={idx}
                                                    skill={skill}
                                                    variant={sharedSkills.includes(skill) ? 'shared' : 'normal'}
                                                    size="sm"
                                                />
                                            ))}
                                        </div>
                                    </div>
                                    <div>
                                        <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">Tools</p>
                                        <div className="flex flex-wrap gap-2">
                                            {employee.tools.map((tool, idx) => (
                                                <SkillChip key={idx} skill={tool} size="sm" />
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </section>
                        </div>

                        {/* Right Column */}
                        <div className="space-y-8">
                            {/* Current Projects */}
                            <section>
                                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                                    <Rocket className="w-5 h-5 mr-2 text-gray-600" />
                                    Current Projects
                                </h3>
                                <div className="space-y-4">
                                    {employee.projects.slice(0, 4).map((project, idx) => (
                                        <div key={idx} className="bg-gray-50 rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors">
                                            <h4 className="font-semibold text-gray-900 mb-1">{project.name}</h4>
                                            <p className="text-sm text-gray-600 mb-2">{project.description}</p>
                                            <div className="flex flex-wrap gap-1">
                                                {project.tech.map((tech, techIdx) => (
                                                    <span key={techIdx} className="px-2 py-0.5 bg-white text-gray-600 text-xs rounded border border-gray-200">
                                                        {tech}
                                                    </span>
                                                ))}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </section>
                        </div>
                    </div>
                </div>

                {/* Footer Actions */}
                <div className="border-t border-gray-200 px-8 py-4 bg-gray-50 flex justify-end space-x-3">
                    <button
                        onClick={onClose}
                        className="px-4 py-2 rounded-lg border-2 border-gray-300 text-gray-700 font-medium hover:bg-gray-100 transition-colors"
                    >
                        Close
                    </button>
                    <button className="px-4 py-2 rounded-lg border-2 border-gray-300 text-gray-700 font-medium hover:bg-gray-100 transition-colors">
                        Message
                    </button>
                    <button className="px-4 py-2 rounded-lg bg-black text-white font-medium hover:bg-gray-800 transition-colors">
                        Connect
                    </button>
                </div>
            </div>

            <style>{`
                @keyframes fade-in {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                @keyframes slide-up {
                    from {
                        opacity: 0;
                        transform: translateY(20px);
                    }
                    to {
                        opacity: 1;
                        transform: translateY(0);
                    }
                }
                .animate-fade-in {
                    animation: fade-in 0.2s ease-out;
                }
                .animate-slide-up {
                    animation: slide-up 0.3s ease-out;
                }
            `}</style>
        </div>
    );
};
