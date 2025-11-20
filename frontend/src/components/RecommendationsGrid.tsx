import React from 'react';
import { EmployeeCard, type Employee } from './EmployeeCard';

interface RecommendationsGridProps {
    recommendations: Employee[];
    onReadMore: (employee: Employee) => void;
}

export const RecommendationsGrid: React.FC<RecommendationsGridProps> = ({ recommendations, onReadMore }) => {
    if (recommendations.length === 0) {
        return null;
    }

    return (
        <div className="mt-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Recommended Connections</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {recommendations.map((emp, index) => (
                    <EmployeeCard key={emp.id || index} employee={emp} onReadMore={onReadMore} />
                ))}
            </div>
        </div>
    );
};
