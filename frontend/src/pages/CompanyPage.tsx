import { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Box,
  Card,
  CardContent,
  TextField,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  Snackbar,
  CircularProgress,
} from '@mui/material';
import { Business, Add, CheckCircle } from '@mui/icons-material';
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

const CompanyPage: React.FC = () => {
  const [companies, setCompanies] = useState<Company[]>([]);
  const [loading, setLoading] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
  
  const [formData, setFormData] = useState({
    company_id: '',
    name: '',
    skills: '',
    experience: '',
    education: '',
  });

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

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);

    try {
      const companyData = {
        company_id: parseInt(formData.company_id),
        name: formData.name,
        requirements: {
          skills: formData.skills.split(',').map(s => s.trim()).filter(Boolean),
          experience: parseInt(formData.experience) || 0,
          education: formData.education.split(',').map(s => s.trim()).filter(Boolean),
        },
      };

      await axios.post('http://localhost:5000/company', companyData);
      
      setSnackbar({
        open: true,
        message: 'Company registered successfully!',
        severity: 'success',
      });
      
      setFormData({
        company_id: '',
        name: '',
        skills: '',
        experience: '',
        education: '',
      });
      
      loadCompanies();
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Error registering company. Please try again.',
        severity: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value,
    });
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
          Company Registration
        </Typography>
        <Typography variant="h6" color="text.secondary">
          Register your company and define job requirements for intelligent candidate matching.
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {/* Registration Form */}
        <Box sx={{ flex: 1, minWidth: '400px' }}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <Business sx={{ mr: 2, color: 'primary.main' }} />
                <Typography variant="h5" component="h2" fontWeight={600}>
                  Register New Company
                </Typography>
              </Box>

              <form onSubmit={handleSubmit}>
                <TextField
                  fullWidth
                  label="Company ID"
                  name="company_id"
                  value={formData.company_id}
                  onChange={handleChange}
                  required
                  type="number"
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="Company Name"
                  name="name"
                  value={formData.name}
                  onChange={handleChange}
                  required
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="Required Skills (comma separated)"
                  name="skills"
                  value={formData.skills}
                  onChange={handleChange}
                  placeholder="e.g., Python, React, Machine Learning"
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="Years of Experience Required"
                  name="experience"
                  value={formData.experience}
                  onChange={handleChange}
                  type="number"
                  sx={{ mb: 3 }}
                />

                <TextField
                  fullWidth
                  label="Education Requirements (comma separated)"
                  name="education"
                  value={formData.education}
                  onChange={handleChange}
                  placeholder="e.g., Computer Science, Engineering"
                  sx={{ mb: 3 }}
                />

                <Button
                  type="submit"
                  variant="contained"
                  size="large"
                  fullWidth
                  disabled={loading}
                  startIcon={loading ? <CircularProgress size={20} /> : <Add />}
                  sx={{ py: 1.5 }}
                >
                  {loading ? 'Registering...' : 'Register Company'}
                </Button>
              </form>
            </CardContent>
          </Card>
        </Box>

        {/* Companies List */}
        <Box sx={{ flex: 1, minWidth: '400px' }}>
          <Card>
            <CardContent sx={{ p: 4 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
                <CheckCircle sx={{ mr: 2, color: 'success.main' }} />
                <Typography variant="h5" component="h2" fontWeight={600}>
                  Registered Companies
                </Typography>
              </Box>

              {companies.length === 0 ? (
                <Alert severity="info">
                  No companies registered yet. Register your first company above!
                </Alert>
              ) : (
                <TableContainer component={Paper} elevation={0}>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>ID</TableCell>
                        <TableCell>Name</TableCell>
                        <TableCell>Skills</TableCell>
                        <TableCell>Experience</TableCell>
                        <TableCell>Education</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {companies.map((company) => (
                        <TableRow key={company.company_id}>
                          <TableCell>{company.company_id}</TableCell>
                          <TableCell>{company.name}</TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {company.requirements.skills.map((skill, index) => (
                                <Chip
                                  key={index}
                                  label={skill}
                                  size="small"
                                  color="primary"
                                  variant="outlined"
                                />
                              ))}
                            </Box>
                          </TableCell>
                          <TableCell>
                            {company.requirements.experience || 0} years
                          </TableCell>
                          <TableCell>
                            <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                              {company.requirements.education.map((edu, index) => (
                                <Chip
                                  key={index}
                                  label={edu}
                                  size="small"
                                  color="secondary"
                                  variant="outlined"
                                />
                              ))}
                            </Box>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
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

export default CompanyPage;