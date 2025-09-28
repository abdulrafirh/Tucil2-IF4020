import React, { useState, useEffect } from 'react';

// Define a type for the API response for better type safety
interface ApiResponse {
  message: string;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

function App() {
  // Use TypeScript to type the state. It can be a string or null initially.
  const [data, setData] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // This effect runs once when the component mounts.
    // We fetch data from the Flask backend's API endpoint.
    fetch(`${API_BASE_URL}/api/data`)
      .then(res => {
        // If the response is not OK (e.g., 404 or 500), throw an error.
        if (!res.ok) {
          throw new Error('Network response was not ok');
        }
        // Parse the JSON response, asserting its type to our interface.
        return res.json() as Promise<ApiResponse>;
      })
      .then(responseData => {
        // On success, update the state with the message from the backend.
        setData(responseData.message);
        setLoading(false);
      })
      .catch(error => {
        // If an error occurs during the fetch, update the error state.
        console.error("Fetch error:", error);
        setError("Failed to fetch data from the backend. Is it running?");
        setLoading(false);
      });
  }, []); // The empty dependency array ensures this effect runs only once.

  // Helper function to conditionally render content based on state
  const renderContent = () => {
    if (loading) {
      return <p className="text-lg text-gray-400 animate-pulse">Loading data from backend...</p>;
    }
    if (error) {
      return <p className="text-lg text-red-400">{error}</p>;
    }
    // Display the fetched data with a label
    return (
      <div>
        <span className="text-cyan-400 font-semibold">Message from Flask:</span>
        <p className="text-lg text-white mt-1 p-3 bg-gray-700 rounded-md">
          {data}
        </p>
      </div>
    );
  }

  return (
    <div className="bg-gray-900 text-white min-h-screen flex items-center justify-center font-sans">
      <div className="text-center p-8 max-w-lg w-full bg-gray-800 rounded-xl shadow-2xl border border-gray-700">
        <h1 className="text-4xl font-bold text-cyan-400 mb-6 tracking-tight">
          React (TS) + Flask App
        </h1>
        <div className="bg-gray-900 p-6 rounded-lg mt-4 border border-gray-600 min-h-[100px] flex items-center justify-center">
          {renderContent()}
        </div>
      </div>
    </div>
  );
}

export default App;