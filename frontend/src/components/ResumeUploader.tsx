import React, { useState, useRef, useEffect } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import mammoth from 'mammoth';
import { X, Send, Paperclip, FileText, Image as ImageIcon, Loader2, AlertCircle } from 'lucide-react';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

// Set worker source
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

interface ResumeUploaderProps {
    onTextExtracted: (data: { text: string; mode: 'resume' | 'search' | 'name_search' }) => void;
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({ onTextExtracted }) => {
    const [inputText, setInputText] = useState('');
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Auto-resize textarea
    useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
        }
    }, [inputText]);

    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            // Validate file type
            const validTypes = [
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'image/png',
                'image/jpeg',
                'image/jpg'
            ];
            if (validTypes.includes(file.type)) {
                setSelectedFile(file);
                setError(null);
            } else {
                setError('Unsupported file type. Please upload PDF, DOC, DOCX, PNG, or JPG.');
            }
        }
        // Reset input so same file can be selected again if needed
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    const removeFile = () => {
        setSelectedFile(null);
    };

    const extractTextFromPdf = async (file: File): Promise<string> => {
        const arrayBuffer = await file.arrayBuffer();
        const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
        let fullText = '';

        for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const textContent = await page.getTextContent();
            const pageText = textContent.items.map((item: any) => item.str).join(' ');
            fullText += pageText + ' ';
        }
        return fullText;
    };

    const extractTextFromDocx = async (file: File): Promise<string> => {
        const arrayBuffer = await file.arrayBuffer();
        const result = await mammoth.extractRawText({ arrayBuffer });
        return result.value;
    };

    const handleSubmit = async () => {
        if (!inputText.trim() && !selectedFile) {
            setError('Please enter text or upload a file.');
            return;
        }

        setIsLoading(true);
        setError(null);

        try {
            let combinedText = inputText.trim();
            let fileText = '';

            if (selectedFile) {
                if (selectedFile.type === 'application/pdf') {
                    fileText = await extractTextFromPdf(selectedFile);
                } else if (selectedFile.type === 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ||
                    selectedFile.type === 'application/msword') {
                    fileText = await extractTextFromDocx(selectedFile);
                } else if (selectedFile.type.startsWith('image/')) {
                    // For images, we currently just append the filename as context
                    // since we don't have OCR configured yet.
                    fileText = `[Attached Image: ${selectedFile.name}]`;
                }

                if (combinedText) {
                    combinedText += '\n\n';
                }
                combinedText += `[Attached File Content (${selectedFile.name})]:\n${fileText}`;
            }

            // Detect search intent
            const searchKeywords = ["find", "search", "show", "who knows", "who has", "people skilled in", "looking for", "expert in"];
            const lowerText = combinedText.toLowerCase();

            let mode: 'resume' | 'search' | 'name_search' = 'resume';

            if (!selectedFile) {
                const isKeywordSearch = searchKeywords.some(keyword => lowerText.includes(keyword));

                if (isKeywordSearch) {
                    mode = 'search';
                } else {
                    // Common technical keywords (skills, languages, frameworks, tools, domains)
                    const technicalKeywords = [
                        // Programming Languages
                        'python', 'java', 'javascript', 'typescript', 'go', 'rust', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
                        // Frontend
                        'react', 'vue', 'angular', 'svelte', 'next.js', 'nextjs', 'html', 'css', 'tailwind',
                        // Backend
                        'node', 'express', 'django', 'flask', 'spring', 'rails',
                        // Databases
                        'sql', 'nosql', 'postgresql', 'postgres', 'mysql', 'mongodb', 'redis', 'elasticsearch',
                        // Cloud & DevOps
                        'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'k8s', 'jenkins', 'ci/cd', 'terraform',
                        // Data & ML
                        'machine learning', 'data science', 'ai', 'deep learning', 'tensorflow', 'pytorch', 'pandas', 'spark',
                        // Other
                        'api', 'rest', 'graphql', 'microservices', 'backend', 'frontend', 'fullstack', 'devops'
                    ];

                    // Check if query matches technical keywords
                    const isTechnicalQuery = technicalKeywords.some(keyword =>
                        lowerText.includes(keyword) || keyword.includes(lowerText)
                    );

                    if (isTechnicalQuery) {
                        mode = 'search';
                    } else {
                        // Name search heuristics (more restrictive):
                        // 1. Short length (< 50 chars)
                        // 2. Only letters, spaces, apostrophes, hyphens
                        // 3. 1-3 words
                        // 4. Looks like a proper name (first letter capitalized or all lowercase)
                        const words = combinedText.trim().split(/\s+/);
                        const isShort = combinedText.length < 50;
                        const isFewWords = words.length >= 1 && words.length <= 3;
                        const isNameLike = /^[a-zA-Z\s'-]+$/.test(combinedText);

                        // Check if it looks like a proper name (at least one capitalized word)
                        const hasCapitalizedWord = words.some(word => word.length > 0 && word[0] === word[0].toUpperCase());

                        if (isShort && isFewWords && isNameLike && hasCapitalizedWord) {
                            mode = 'name_search';
                        } else {
                            // Default to search mode for ambiguous cases
                            mode = 'search';
                        }
                    }
                }
            }

            onTextExtracted({
                text: combinedText,
                mode: mode
            });
            // Clear inputs after successful submission
            setInputText('');
            setSelectedFile(null);
            if (textareaRef.current) {
                textareaRef.current.style.height = 'auto';
            }
        } catch (err) {
            console.error(err);
            setError('Failed to process input. Please try again.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    const getFileIcon = (type: string) => {
        if (type.includes('pdf')) return <FileText className="w-4 h-4 text-red-500" />;
        if (type.includes('word') || type.includes('document')) return <FileText className="w-4 h-4 text-blue-500" />;
        if (type.includes('image')) return <ImageIcon className="w-4 h-4 text-green-500" />;
        return <Paperclip className="w-4 h-4 text-gray-500" />;
    };

    return (
        <div className="w-full max-w-3xl mx-auto">
            <div className="relative flex flex-col bg-white border border-gray-300 rounded-2xl shadow-sm hover:border-gray-400 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all">

                {/* File Preview Area */}
                {selectedFile && (
                    <div className="px-4 pt-4 pb-2">
                        <div className="inline-flex items-center gap-2 bg-gray-100 px-3 py-1.5 rounded-lg text-sm text-gray-700 group">
                            {getFileIcon(selectedFile.type)}
                            <span className="max-w-[200px] truncate font-medium">{selectedFile.name}</span>
                            <button
                                onClick={removeFile}
                                className="ml-1 p-0.5 rounded-full hover:bg-gray-200 text-gray-500 hover:text-gray-700 transition-colors"
                                aria-label="Remove attachment"
                            >
                                <X className="w-3.5 h-3.5" />
                            </button>
                        </div>
                    </div>
                )}

                {/* Input Area */}
                <div className="flex items-end gap-2 p-3">
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileSelect}
                        className="hidden"
                        accept=".pdf,.doc,.docx,.png,.jpg,.jpeg"
                    />

                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-full transition-colors flex-shrink-0"
                        aria-label="Upload attachment"
                        title="Attach file"
                    >
                        <Paperclip className="w-5 h-5" />
                    </button>

                    <textarea
                        ref={textareaRef}
                        value={inputText}
                        onChange={(e) => setInputText(e.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Type your background or upload a resume..."
                        className="flex-1 max-h-[200px] py-2 bg-transparent border-none focus:ring-0 resize-none text-gray-900 placeholder-gray-500 leading-relaxed"
                        rows={1}
                        aria-label="Resume input box"
                        disabled={isLoading}
                    />

                    <button
                        onClick={handleSubmit}
                        disabled={isLoading || (!inputText.trim() && !selectedFile)}
                        className={`p-2 rounded-lg transition-all flex-shrink-0 ${inputText.trim() || selectedFile
                            ? 'bg-black text-white hover:bg-gray-800'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                            }`}
                        aria-label="Submit"
                        title="Analyze"
                    >
                        {isLoading ? (
                            <Loader2 className="w-5 h-5 animate-spin" />
                        ) : (
                            <Send className="w-5 h-5" />
                        )}
                    </button>
                </div>
            </div>

            {/* Error Message */}
            {error && (
                <div className="mt-3 flex items-center gap-2 text-sm text-red-600 animate-in fade-in slide-in-from-top-1">
                    <AlertCircle className="w-4 h-4" />
                    {error}
                </div>
            )}

            <div className="mt-3 text-center text-xs text-gray-400">
                Supported formats: PDF, DOCX, PNG, JPG
            </div>
        </div>
    );
};
