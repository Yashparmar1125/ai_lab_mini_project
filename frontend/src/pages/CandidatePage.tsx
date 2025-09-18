import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  LinearProgress,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
  Divider,
  Paper,
} from '@mui/material';
import { Person, Upload, Assessment } from '@mui/icons-material';
import axios from 'axios';

interface Company {
  company_id: number;
  name: string;
  requirements: {
    skills: string[];
    experience: number;
    education: string[];
  };
}

interface AnalysisResult {
  fit_score: number;
  fit_breakdown: {
    skills: number;
    experience: number;
    education: number;
    semantic: number;
    matched_skills: string[];
    missing_skills: string[];
  };
  resume_quality: {
    grammar_issues: string[];
    suggestions: string[];
    readability: {
      flesch_reading_ease?: number;
      smog_index?: number;
      avg_sentence_length?: number;
    };
  };
  comprehensive_analysis?: {
    overall_score: number;
    quality_analysis: any;
    contact_analysis: {
      email: boolean;
      phone: boolean;
      linkedin: boolean;
      github: boolean;
      issues: string[];
      completeness_score: number;
    };
    summary_analysis: {
      found: boolean;
      text: string;
      word_count: number;
      issues: string[];
      suggestions: string[];
    };
    ats_analysis: {
      issues: string[];
      suggestions: string[];
      ats_score: number;
    };
    keyword_analysis?: {
      keyword_counts: any;
      overall_density: number;
      recommendations: string[];
    };
    recommendations: {
      priority: string[];
      quick_wins: string[];
    };
  };
}

const CandidatePage: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [selectedCompany, setSelectedCompany] = useState<number | ''>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });

  useEffect(() => {
    loadCompanies();
  }, []);

  const loadCompanies = async () => {
    try {
      const response = await axios.get('http://localhost:5000/companies');
      setCompanies(response.data);
    } catch (error) {
      console.error('Error loading companies:', error);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) {
      setSnackbar({
        open: true,
        message: 'Please select a resume file.',
        severity: 'error',
      });
      return;
    }

    setLoading(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);

      if (selectedCompany) {
        // Analyze against specific company
        const uploadResponse = await axios.post('http://localhost:5000/upload_resume', formData);
        const companyResponse = await axios.get(`http://localhost:5000/company/${selectedCompany}`);
        
        const analysisResponse = await axios.post('http://localhost:5000/analyze', {
          requirements: companyResponse.data.requirements,
          resume_text: uploadResponse.data.extracted_text,
        });
        
        setAnalysisResult(analysisResponse.data);
      } else {
        // Just analyze resume quality
        const uploadResponse = await axios.post('http://localhost:5000/upload_resume', formData);
        setAnalysisResult({
          fit_score: 0,
          fit_breakdown: {
            skills: 0,
            experience: 0,
            education: 0,
            semantic: 0,
            matched_skills: [],
            missing_skills: [],
          },
          resume_quality: uploadResponse.data.resume_quality,
        });
      }

      setSnackbar({
        open: true,
        message: 'Analysis completed successfully!',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error analyzing resume. Please try again.',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h2"
          component="h1"
          gutterBottom
          sx={{ fontWeight: 600, mb: 2 }}
        >
          Candidate Application
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Upload your resume and get intelligent feedback or match against company requirements.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {/* Upload Section */}
        <Box sx={{ flex: 1, minWidth: '400px' }}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Person sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h5" component="h2" fontWeight={600}>
                  Upload Resume
                </Typography>
              </Box>

              <FormControl fullWidth sx={{ mb: 3 }}>
                <InputLabel>Select Company (Optional)</InputLabel>
                <Select
                  value={selectedCompany}
                  onChange={(e) => setSelectedCompany(e.target.value as number | '')}
                  label="Select Company (Optional)"
                >
                  <MenuItem value="">
                    <em>Just analyze resume quality</em>
                  </MenuItem>
                  {companies.map((company) => (
                    <MenuItem key={company.company_id} value={company.company_id}>
                      {company.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <Box sx={{ mb: 3 }}>
                <input
                  accept=".pdf,.docx"
                  style={{ display: 'none' }}
                  id="resume-upload"
                  type="file"
                  onChange={handleFileChange}
                />
                <label htmlFor="resume-upload">
                  <Button
                    variant="outlined"
                    component="span"
                    startIcon={<Upload />}
                    fullWidth
                    sx={{ py: 2 }}
                  >
                    {selectedFile ? selectedFile.name : 'Choose Resume File (PDF/DOCX)'}
                  </Button>
                </label>
              </Box>

              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleSubmit}
                disabled={loading || !selectedFile}
                startIcon={loading ? <CircularProgress size={20} /> : <Assessment />}
                sx={{ py: 1.5 }}
              >
                {loading ? 'Analyzing...' : 'Analyze Resume'}
              </Button>
            </CardContent>
          </Card>
        </Box>

        {/* Results Section */}
        <Box sx={{ flex: 1, minWidth: '400px' }}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Assessment sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h5" component="h2" fontWeight={600}>
                  Analysis Results
                </Typography>
              </Box>

              {loading ? (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <CircularProgress size={60} />
                  <Typography variant="h6" sx={{ mt: 2 }}>
                    Analyzing your resume...
                  </Typography>
                </Box>
              ) : analysisResult ? (
                <Box>
                  {/* Fit Score */}
                  {analysisResult.fit_score > 0 && (
                    <Box sx={{ mb: 4 }}>
                      <Typography variant="h6" gutterBottom>
                        Overall Fit Score
                      </Typography>
                      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                        <Typography variant="h3" sx={{ mr: 2, fontWeight: 700 }}>
                          {analysisResult.fit_score.toFixed(1)}%
                        </Typography>
                        <Chip
                          label={getScoreColor(analysisResult.fit_score)}
                          color={getScoreColor(analysisResult.fit_score)}
                          variant="outlined"
                        />
                      </Box>
                      <LinearProgress
                        variant="determinate"
                        value={analysisResult.fit_score}
                        color={getScoreColor(analysisResult.fit_score)}
                        sx={{ height: 10, borderRadius: 5 }}
                      />
                    </Box>
                  )}

                  {/* Score Breakdown */}
                  {analysisResult.fit_score > 0 && (
                    <Box sx={{ mb: 4 }}>
                      <Typography variant="h6" gutterBottom>
                        Score Breakdown
                      </Typography>
                      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2 }}>
                        <Paper sx={{ p: 2, textAlign: 'center', flex: 1, minWidth: '120px' }}>
                          <Typography variant="h4" color="primary.main">
                            {analysisResult.fit_breakdown.skills}%
                          </Typography>
                          <Typography variant="body2">Skills Match</Typography>
                        </Paper>
                        <Paper sx={{ p: 2, textAlign: 'center', flex: 1, minWidth: '120px' }}>
                          <Typography variant="h4" color="primary.main">
                            {analysisResult.fit_breakdown.experience}%
                          </Typography>
                          <Typography variant="body2">Experience</Typography>
                        </Paper>
                        <Paper sx={{ p: 2, textAlign: 'center', flex: 1, minWidth: '120px' }}>
                          <Typography variant="h4" color="primary.main">
                            {analysisResult.fit_breakdown.education}%
                          </Typography>
                          <Typography variant="body2">Education</Typography>
                        </Paper>
                        <Paper sx={{ p: 2, textAlign: 'center', flex: 1, minWidth: '120px' }}>
                          <Typography variant="h4" color="primary.main">
                            {analysisResult.fit_breakdown.semantic}%
                          </Typography>
                          <Typography variant="body2">Semantic</Typography>
                        </Paper>
                      </Box>
                    </Box>
                  )}

                  {/* Skills Analysis */}
                  {analysisResult.fit_score > 0 && (
                    <Box sx={{ mb: 4 }}>
                      <Typography variant="h6" gutterBottom>
                        Skills Analysis
                      </Typography>
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="success.main" gutterBottom>
                          Matched Skills:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {analysisResult.fit_breakdown.matched_skills.map((skill, index) => (
                            <Chip key={index} label={skill} color="success" size="small" />
                          ))}
                        </Box>
                      </Box>
                      <Box>
                        <Typography variant="subtitle2" color="error.main" gutterBottom>
                          Missing Skills:
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                          {analysisResult.fit_breakdown.missing_skills.map((skill, index) => (
                            <Chip key={index} label={skill} color="error" size="small" />
                          ))}
                        </Box>
                      </Box>
                    </Box>
                  )}

                  <Divider sx={{ my: 3 }} />

                  {/* Comprehensive Analysis */}
                  {analysisResult.comprehensive_analysis && (
                    <Box sx={{ mb: 4 }}>
                      <Typography variant="h6" gutterBottom>
                        Comprehensive Resume Analysis
                      </Typography>
                      
                      {/* Overall Score */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Overall Resume Score
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h3" sx={{ mr: 2, fontWeight: 700 }}>
                            {analysisResult.comprehensive_analysis.overall_score}%
                          </Typography>
                          <Chip
                            label={getScoreColor(analysisResult.comprehensive_analysis.overall_score)}
                            color={getScoreColor(analysisResult.comprehensive_analysis.overall_score)}
                            variant="outlined"
                          />
                        </Box>
                        <LinearProgress
                          variant="determinate"
                          value={analysisResult.comprehensive_analysis.overall_score}
                          color={getScoreColor(analysisResult.comprehensive_analysis.overall_score)}
                          sx={{ height: 10, borderRadius: 5 }}
                        />
                      </Box>

                      {/* Contact Information */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Contact Information ({analysisResult.comprehensive_analysis.contact_analysis.completeness_score}%)
                        </Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                          <Chip
                            label="Email"
                            color={analysisResult.comprehensive_analysis.contact_analysis.email ? "success" : "error"}
                            size="small"
                          />
                          <Chip
                            label="Phone"
                            color={analysisResult.comprehensive_analysis.contact_analysis.phone ? "success" : "error"}
                            size="small"
                          />
                          <Chip
                            label="LinkedIn"
                            color={analysisResult.comprehensive_analysis.contact_analysis.linkedin ? "success" : "warning"}
                            size="small"
                          />
                          <Chip
                            label="GitHub"
                            color={analysisResult.comprehensive_analysis.contact_analysis.github ? "success" : "warning"}
                            size="small"
                          />
                        </Box>
                        {analysisResult.comprehensive_analysis.contact_analysis.issues.map((issue, index) => (
                          <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                            {issue}
                          </Alert>
                        ))}
                      </Box>

                      {/* Professional Summary */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Professional Summary
                        </Typography>
                        {analysisResult.comprehensive_analysis.summary_analysis.found ? (
                          <Box>
                            <Alert severity="success" sx={{ mb: 1 }}>
                              Professional summary found ({analysisResult.comprehensive_analysis.summary_analysis.word_count} words)
                            </Alert>
                            {analysisResult.comprehensive_analysis.summary_analysis.suggestions.map((suggestion, index) => (
                              <Alert key={index} severity="info" sx={{ mb: 1 }}>
                                {suggestion}
                              </Alert>
                            ))}
                          </Box>
                        ) : (
                          <Alert severity="error">
                            Missing professional summary section
                          </Alert>
                        )}
                      </Box>

                      {/* ATS Optimization */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          ATS Optimization ({analysisResult.comprehensive_analysis.ats_analysis.ats_score}%)
                        </Typography>
                        {analysisResult.comprehensive_analysis.ats_analysis.issues.length > 0 ? (
                          analysisResult.comprehensive_analysis.ats_analysis.issues.map((issue, index) => (
                            <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                              {issue}
                            </Alert>
                          ))
                        ) : (
                          <Alert severity="success">Resume is ATS-optimized!</Alert>
                        )}
                      </Box>

                      {/* Priority Recommendations */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Priority Recommendations
                        </Typography>
                        {analysisResult.comprehensive_analysis.recommendations.priority.map((rec, index) => (
                          <Alert key={index} severity="info" sx={{ mb: 1 }}>
                            {rec}
                          </Alert>
                        ))}
                      </Box>

                      {/* Quick Wins */}
                      <Box sx={{ mb: 3 }}>
                        <Typography variant="subtitle1" gutterBottom>
                          Quick Wins
                        </Typography>
                        {analysisResult.comprehensive_analysis.recommendations.quick_wins.map((win, index) => (
                          <Alert key={index} severity="success" sx={{ mb: 1 }}>
                            {win}
                          </Alert>
                        ))}
                      </Box>
                    </Box>
                  )}

                  <Divider sx={{ my: 3 }} />

                  {/* Basic Resume Quality */}
                  <Box>
                    <Typography variant="h6" gutterBottom>
                      Grammar & Writing Quality
                    </Typography>
                    
                    {analysisResult.resume_quality.grammar_issues.length > 0 ? (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="subtitle2" color="error.main" gutterBottom>
                          Grammar Issues:
                        </Typography>
                        {analysisResult.resume_quality.grammar_issues.map((issue, index) => (
                          <Alert key={index} severity="warning" sx={{ mb: 1 }}>
                            {issue}
                          </Alert>
                        ))}
                      </Box>
                    ) : (
                      <Alert severity="success" sx={{ mb: 2 }}>
                        No significant grammar issues found!
                      </Alert>
                    )}

                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Writing Suggestions:
                      </Typography>
                      {analysisResult.resume_quality.suggestions.map((suggestion, index) => (
                        <Alert key={index} severity="info" sx={{ mb: 1 }}>
                          {suggestion}
                        </Alert>
                      ))}
                    </Box>
                  </Box>
                </Box>
              ) : (
                <Alert severity="info">
                  Upload a resume file to get started with the analysis.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Box>
      </Box>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
      >
        <Alert
          onClose={() => setSnackbar({ ...snackbar, open: false })}
          severity={snackbar.severity}
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default CandidatePage;