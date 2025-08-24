import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Upload, FileText, AlertCircle, CheckCircle, Clock } from 'lucide-react';
import { Alert, AlertDescription } from '../ui/alert';

const TeaScoresCalculator = () => {
  const [file, setFile] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain'];
      if (!allowedTypes.includes(selectedFile.type)) {
        setError('Please upload a PDF, Word document (.doc/.docx), or text file.');
        return;
      }
      
      // Validate file size (10MB limit)
      if (selectedFile.size > 10 * 1024 * 1024) {
        setError('File size must be less than 10MB.');
        return;
      }
      
      setFile(selectedFile);
      setError(null);
      setResults(null);
    }
  };

  const calculateScores = async () => {
    if (!file) {
      setError('Please select a file first.');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch('/api/ai-analysis/calculate-tea-scores', {
        method: 'POST',
        body: formData,
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Failed to calculate scores');
      }

      setResults(data);
    } catch (err) {
      setError(err.message || 'An error occurred while calculating scores.');
    } finally {
      setIsLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-yellow-600';
    if (score >= 4) return 'text-orange-600';
    return 'text-red-600';
  };

  const getScoreLabel = (score) => {
    if (score >= 8) return 'Excellent';
    if (score >= 6) return 'Good';
    if (score >= 4) return 'Fair';
    return 'Poor';
  };

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="h-6 w-6" />
            TEA Scores Calculator
          </CardTitle>
          <CardDescription>
            Calculate Transparency, Explainability, and Accountability scores for your policy document using AI analysis.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* File Upload */}
          <div className="space-y-2">
            <label htmlFor="file-upload" className="text-sm font-medium">
              Upload Policy Document
            </label>
            <div className="flex items-center space-x-2">
              <input
                id="file-upload"
                type="file"
                accept=".pdf,.doc,.docx,.txt"
                onChange={handleFileChange}
                className="flex-1 text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                disabled={isLoading}
              />
              <Button 
                onClick={calculateScores} 
                disabled={!file || isLoading}
                className="flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Clock className="h-4 w-4 animate-spin" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Upload className="h-4 w-4" />
                    Calculate Scores
                  </>
                )}
              </Button>
            </div>
            {file && (
              <p className="text-sm text-gray-600">
                Selected: {file.name} ({(file.size / 1024 / 1024).toFixed(2)} MB)
              </p>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Results */}
          {results && (
            <div className="space-y-6">
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  Analysis completed successfully! Scores calculated using AWS Bedrock.
                </AlertDescription>
              </Alert>

              {/* Scores Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Transparency</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      <span className={getScoreColor(results.scores.transparency_score)}>
                        {results.scores.transparency_score}/10
                      </span>
                    </div>
                    <p className={`text-sm ${getScoreColor(results.scores.transparency_score)}`}>
                      {getScoreLabel(results.scores.transparency_score)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Explainability</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      <span className={getScoreColor(results.scores.explainability_score)}>
                        {results.scores.explainability_score}/10
                      </span>
                    </div>
                    <p className={`text-sm ${getScoreColor(results.scores.explainability_score)}`}>
                      {getScoreLabel(results.scores.explainability_score)}
                    </p>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-2">
                    <CardTitle className="text-lg">Accountability</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="text-3xl font-bold">
                      <span className={getScoreColor(results.scores.accountability_score)}>
                        {results.scores.accountability_score}/10
                      </span>
                    </div>
                    <p className={`text-sm ${getScoreColor(results.scores.accountability_score)}`}>
                      {getScoreLabel(results.scores.accountability_score)}
                    </p>
                  </CardContent>
                </Card>
              </div>

              {/* Detailed Analysis */}
              <div className="space-y-4">
                <h3 className="text-xl font-semibold">Detailed Analysis</h3>
                
                {/* Transparency Analysis */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Transparency Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {results.detailed_analysis.transparency_analysis.map((item, index) => (
                        <div key={index} className="border-l-4 border-blue-500 pl-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-medium text-sm">{item.question}</p>
                              <p className="text-sm text-gray-600 mt-1">{item.justification}</p>
                            </div>
                            <div className="ml-4 text-right">
                              <span className="text-lg font-bold">{item.score}/2</span>
                              <p className="text-sm text-gray-500">{item.answer}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Explainability Analysis */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Explainability Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {results.detailed_analysis.explainability_analysis.map((item, index) => (
                        <div key={index} className="border-l-4 border-green-500 pl-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-medium text-sm">{item.question}</p>
                              <p className="text-sm text-gray-600 mt-1">{item.justification}</p>
                            </div>
                            <div className="ml-4 text-right">
                              <span className="text-lg font-bold">{item.score}/2</span>
                              <p className="text-sm text-gray-500">{item.answer}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>

                {/* Accountability Analysis */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Accountability Analysis</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      {results.detailed_analysis.accountability_analysis.map((item, index) => (
                        <div key={index} className="border-l-4 border-purple-500 pl-4">
                          <div className="flex justify-between items-start">
                            <div className="flex-1">
                              <p className="font-medium text-sm">{item.question}</p>
                              <p className="text-sm text-gray-600 mt-1">{item.justification}</p>
                            </div>
                            <div className="ml-4 text-right">
                              <span className="text-lg font-bold">{item.score}/2</span>
                              <p className="text-sm text-gray-500">{item.answer}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Form Data for Auto-fill */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Form Auto-fill Data</CardTitle>
                  <CardDescription>
                    Use these scores to automatically fill your policy submission form.
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-50 p-4 rounded-lg">
                    <p className="text-sm text-gray-600 mb-2">Copy these values to your form:</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <strong>Transparency Score:</strong> {results.form_data.transparency_score}
                      </div>
                      <div>
                        <strong>Explainability Score:</strong> {results.form_data.explainability_score}
                      </div>
                      <div>
                        <strong>Accountability Score:</strong> {results.form_data.accountability_score}
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default TeaScoresCalculator;
