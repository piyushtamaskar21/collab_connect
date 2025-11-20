import React, { useCallback, useState } from 'react';
import * as pdfjsLib from 'pdfjs-dist';
import { Upload, Loader2, AlertCircle } from 'lucide-react';
import pdfWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';

// Set worker source
pdfjsLib.GlobalWorkerOptions.workerSrc = pdfWorker;

interface ResumeUploaderProps {
    onTextExtracted: (text: string) => void;
}

export const ResumeUploader: React.FC<ResumeUploaderProps> = ({ onTextExtracted }) => {
    const [isDragging, setIsDragging] = useState(false);
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const extractText = async (file: File) => {
        setIsLoading(true);
        setError(null);
        try {
            const arrayBuffer = await file.arrayBuffer();
            const pdf = await pdfjsLib.getDocument({ data: arrayBuffer }).promise;
            let fullText = '';

            for (let i = 1; i <= pdf.numPages; i++) {
                const page = await pdf.getPage(i);
                const textContent = await page.getTextContent();
                const pageText = textContent.items.map((item: any) => item.str).join(' ');
                fullText += pageText + ' ';
            }

            onTextExtracted(fullText);
        } catch (err) {
            console.error(err);
            setError('Failed to extract text from PDF. Please try another file.');
        } finally {
            setIsLoading(false);
        }
    };

    const handleDrop = useCallback((e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        const file = e.dataTransfer.files[0];
        if (file && file.type === 'application/pdf') {
            extractText(file);
        } else {
            setError('Please upload a PDF file.');
        }
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            extractText(file);
        }
    };

    return (
        <div className="w-full max-w-2xl mx-auto">
            <div
                className={`relative border-2 border-dashed rounded-xl p-8 transition-all duration-200 ease-in-out
          ${isDragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'}
          ${isLoading ? 'opacity-50 pointer-events-none' : ''}
        `}
                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                onDragLeave={() => setIsDragging(false)}
                onDrop={handleDrop}
            >
                <div className="flex flex-col items-center justify-center text-center space-y-4">
                    <div className="p-4 bg-blue-100 rounded-full text-blue-600">
                        {isLoading ? <Loader2 className="w-8 h-8 animate-spin" /> : <Upload className="w-8 h-8" />}
                    </div>

                    <div>
                        <h3 className="text-lg font-semibold text-gray-900">
                            {isLoading ? 'Processing Resume...' : 'Upload Resume'}
                        </h3>
                        <p className="text-sm text-gray-500 mt-1">
                            Drag and drop your PDF here, or click to browse
                        </p>
                    </div>

                    <input
                        type="file"
                        accept=".pdf"
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                        onChange={handleFileChange}
                        disabled={isLoading}
                    />
                </div>
            </div>

            {error && (
                <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center text-red-700">
                    <AlertCircle className="w-5 h-5 mr-2" />
                    {error}
                </div>
            )}
        </div>
    );
};
