import React from 'react';
import { Briefcase } from 'lucide-react';
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

export interface Employee {
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

interface EmployeeCardProps {
    employee: Employee;
    onReadMore: (employee: Employee) => void;
}

// Color palette for left border accents
const accentColors = [
    'border-l-blue-500',
    'border-l-emerald-500',
    'border-l-cyan-500',
    'border-l-indigo-600',
    'border-l-teal-500'
];

export const EmployeeCard: React.FC<EmployeeCardProps> = ({ employee, onReadMore }) => {
    // Assign color based on employee name hash for consistency
    const colorIndex = employee.name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0) % accentColors.length;
    const accentColor = accentColors[colorIndex];

    const sharedSkills = employee.resumeMatch?.sharedSkills || [];

    return (
        <div className={`bg-white rounded-sm shadow-sm hover:shadow-md transition-shadow duration-200 border-l-4 ${accentColor} overflow-hidden flex flex-col p-6`}>
            {/* Header with Avatar and Name */}
            <div className="flex items-start space-x-4 mb-3">
                <img
                    src={employee.avatarUrl}
                    alt={employee.name}
                    className="w-16 h-16 rounded-full object-cover flex-shrink-0"
                />
                <div className="flex-1 min-w-0">
                    <h3 className="text-lg font-semibold text-black mb-1 truncate">{employee.name}</h3>
                    <div className="flex items-center text-sm text-gray-600 mb-1">
                        <Briefcase className="w-3.5 h-3.5 mr-1.5 flex-shrink-0" />
                        <span className="truncate">{employee.title}</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="inline-block bg-gray-100 text-gray-700 px-2.5 py-0.5 rounded text-xs font-medium">
                            {(employee.matchScore * 100).toFixed(0)}% Match
                        </div>
                    </div>
                </div>
            </div>

            {/* Short Match Explanation */}
            <div className="mb-3">
                <p className="text-xs text-gray-600 leading-relaxed line-clamp-2">
                    {employee.summary}
                </p>
            </div>

            {/* Skills with Highlighting */}
            <div className="flex flex-wrap gap-2 mb-5">
                {employee.skills.slice(0, 6).map((skill, index) => (
                    <SkillChip
                        key={index}
                        skill={skill}
                        variant={sharedSkills.includes(skill) ? 'shared' : 'normal'}
                        size="sm"
                    />
                ))}
                {employee.skills.length > 6 && (
                    <span className="px-2 py-0.5 text-xs text-gray-500">
                        +{employee.skills.length - 6} more
                    </span>
                )}
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-auto pt-4 border-t border-gray-100">
                <button className="flex-1 py-2 px-3 rounded border border-gray-300 text-gray-700 font-medium text-sm hover:bg-gray-50 transition-colors">
                    Message
                </button>
                <button
                    onClick={() => onReadMore(employee)}
                    className="flex-1 py-2 px-3 rounded border border-gray-300 text-gray-700 font-medium text-sm hover:bg-gray-50 transition-colors"
                >
                    Read More
                </button>
                <button className="flex-1 py-2 px-3 rounded bg-black text-white font-medium text-sm hover:bg-gray-800 transition-colors">
                    Connect
                </button>
            </div>
        </div>
    );
};
