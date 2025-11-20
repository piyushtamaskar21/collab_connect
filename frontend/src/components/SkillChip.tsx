import React from 'react';

interface SkillChipProps {
    skill: string;
    variant?: 'normal' | 'shared';
    size?: 'sm' | 'md';
}

export const SkillChip: React.FC<SkillChipProps> = ({ skill, variant = 'normal', size = 'md' }) => {
    const baseClasses = "inline-block font-medium rounded";

    const sizeClasses = size === 'sm'
        ? "px-2 py-0.5 text-xs"
        : "px-2.5 py-1 text-xs";

    const variantClasses = variant === 'shared'
        ? "bg-blue-50 text-blue-700 border-2 border-blue-300 font-semibold"
        : "bg-gray-50 text-gray-700 border border-gray-200";

    return (
        <span className={`${baseClasses} ${sizeClasses} ${variantClasses}`}>
            {skill}
        </span>
    );
};
