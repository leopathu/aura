'use client';

import { useState, useEffect } from 'react';

interface ApiData {
  message: string;
  data: string;
}

export default function Home() {
  const [backendStatus, setBackendStatus] = useState<string>('Checking...');
  const [apiData, setApiData] = useState<ApiData | null>(null);

  useEffect(() => {
    // Check backend health
    const checkBackend = async () => {
      try {
        const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/health');
        if (response.ok) {
          const data = await response.json();
          setBackendStatus(`✅ ${data.status} - ${data.service}`);
        } else {
          setBackendStatus('❌ Backend not responding');
        }
      } catch {
        setBackendStatus('❌ Connection failed');
      }
    };

    // Test API endpoint
    const testApi = async () => {
      try {
        const response = await fetch(process.env.NEXT_PUBLIC_API_URL + '/api/test');
        if (response.ok) {
          const data = await response.json();
          setApiData(data);
        }
      } catch {
        console.error('API test failed');
      }
    };

    checkBackend();
    testApi();
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <h1 className="text-6xl font-bold text-gray-900 dark:text-white mb-4">
            Aura
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 mb-8">
            Augmented Understanding & Retrieval Assistant
          </p>
          
          <div className="max-w-4xl mx-auto">
            <div className="grid md:grid-cols-2 gap-8">
              {/* Frontend Status */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                  Frontend
                </h2>
                <div className="space-y-2 text-left">
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Framework:</span> Next.js
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Status:</span> ✅ Running
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Port:</span> 3000
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Styling:</span> Tailwind CSS
                  </p>
                </div>
              </div>

              {/* Backend Status */}
              <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
                  Backend
                </h2>
                <div className="space-y-2 text-left">
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Framework:</span> FastAPI
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Status:</span> {backendStatus}
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Port:</span> 8000
                  </p>
                  <p className="text-gray-600 dark:text-gray-300">
                    <span className="font-medium">Database:</span> PostgreSQL
                  </p>
                </div>
              </div>
            </div>

            {/* API Test Results */}
            {apiData && (
              <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
                <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  API Test Results
                </h3>
                <pre className="bg-gray-100 dark:bg-gray-700 rounded p-4 text-sm overflow-x-auto">
                  {JSON.stringify(apiData, null, 2)}
                </pre>
              </div>
            )}

            {/* Getting Started */}
            <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6">
              <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                Getting Started
              </h3>
              <div className="text-left space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">Start with Docker:</h4>
                  <code className="bg-gray-100 dark:bg-gray-700 rounded px-2 py-1 text-sm">
                    docker compose up -d
                  </code>
                </div>
                <div>
                  <h4 className="font-medium text-gray-900 dark:text-white">Access Services:</h4>
                  <ul className="list-disc list-inside text-gray-600 dark:text-gray-300 ml-4">
                    <li>Frontend: <a href="http://localhost:3000" className="text-blue-600 hover:underline">http://localhost:3000</a></li>
                    <li>Backend API: <a href="http://localhost:8000" className="text-blue-600 hover:underline">http://localhost:8000</a></li>
                    <li>API Docs: <a href="http://localhost:8000/docs" className="text-blue-600 hover:underline">http://localhost:8000/docs</a></li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
