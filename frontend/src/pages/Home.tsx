import {
  Container,
  Typography,
  Box,
  Button,
  Card,
  CardContent,
  Paper,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  Business,
  Person,
  AutoAwesome,
  Speed,
  Insights,
} from '@mui/icons-material';

const Home: React.FC = () => {
  const navigate = useNavigate();

  const features = [
    {
      icon: <AutoAwesome sx={{ fontSize: 40, color: 'primary.main' }} />,
      title: 'AI-Powered Matching',
      description: 'Advanced semantic analysis matches candidates with 95% accuracy using machine learning algorithms.',
    },
    {
      icon: <Insights sx={{ fontSize: 40, color: 'secondary.main' }} />,
      title: 'Comprehensive Analysis',
      description: 'Get detailed feedback on ATS optimization, keyword density, contact info, and professional summary.',
    },
    {
      icon: <Speed sx={{ fontSize: 40, color: 'success.main' }} />,
      title: '10x Faster Screening',
      description: 'Reduce hiring time from weeks to hours with automated resume analysis and scoring.',
    },
  ];

  return (
    <Box>
      {/* Hero Section */}
      <Paper
        elevation={0}
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 8,
          mb: 6,
        }}
      >
        <Container maxWidth="lg">
          <Box textAlign="center" py={4}>
            <Typography
              variant="h1"
              component="h1"
              gutterBottom
              sx={{
                fontWeight: 700,
                fontSize: { xs: '2.5rem', md: '3.5rem' },
                mb: 3,
              }}
            >
              Streamline Your Hiring with AI
            </Typography>
            <Typography
              variant="h5"
              component="p"
              sx={{
                maxWidth: '800px',
                mx: 'auto',
                mb: 4,
                opacity: 0.9,
                fontWeight: 400,
              }}
            >
              Our intelligent platform helps companies find the best talent and empowers candidates with valuable resume insights.
            </Typography>
            <Box sx={{ display: 'flex', gap: 3, justifyContent: 'center', flexWrap: 'wrap' }}>
              <Button
                variant="contained"
                size="large"
                startIcon={<Business />}
                onClick={() => navigate('/company')}
                sx={{
                  px: 4,
                  py: 2,
                  fontSize: '1.1rem',
                  backgroundColor: 'white',
                  color: 'primary.main',
                  '&:hover': {
                    backgroundColor: 'grey.100',
                  },
                }}
              >
                For Companies: Register & Define Roles
              </Button>
              <Button
                variant="outlined"
                size="large"
                startIcon={<Person />}
                onClick={() => navigate('/candidate')}
                sx={{
                  px: 4,
                  py: 2,
                  fontSize: '1.1rem',
                  borderColor: 'white',
                  color: 'white',
                  '&:hover': {
                    borderColor: 'white',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)',
                  },
                }}
              >
                For Candidates: Upload Resume & Get Feedback
              </Button>
            </Box>
          </Box>
        </Container>
      </Paper>

      {/* Features Section */}
      <Container maxWidth="lg" sx={{ mb: 8 }}>
        <Typography
          variant="h2"
          component="h2"
          textAlign="center"
          gutterBottom
          sx={{ mb: 6, fontWeight: 600 }}
        >
          Why Choose Our Platform?
        </Typography>
        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4, justifyContent: 'center' }}>
          {features.map((feature, index) => (
            <Card
              key={index}
              sx={{
                width: { xs: '100%', md: '300px' },
                textAlign: 'center',
                p: 3,
                transition: 'all 0.3s ease',
                '&:hover': {
                  boxShadow: '0 8px 30px rgba(0, 0, 0, 0.15)',
                  transform: 'translateY(-5px)',
                },
              }}
            >
              <CardContent>
                <Box sx={{ mb: 2 }}>
                  {feature.icon}
                </Box>
                <Typography
                  variant="h5"
                  component="h3"
                  gutterBottom
                  sx={{ fontWeight: 600, mb: 2 }}
                >
                  {feature.title}
                </Typography>
                <Typography
                  variant="body1"
                  color="text.secondary"
                  sx={{ lineHeight: 1.6 }}
                >
                  {feature.description}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </Box>
      </Container>

      {/* Stats Section */}
      <Paper
        elevation={0}
        sx={{
          backgroundColor: 'grey.50',
          py: 6,
        }}
      >
        <Container maxWidth="lg">
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 4, justifyContent: 'center', textAlign: 'center' }}>
            <Box sx={{ minWidth: '200px' }}>
              <Typography variant="h3" component="div" color="primary.main" fontWeight={700}>
                95%
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Accuracy Rate
              </Typography>
            </Box>
            <Box sx={{ minWidth: '200px' }}>
              <Typography variant="h3" component="div" color="primary.main" fontWeight={700}>
                10x
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Faster Screening
              </Typography>
            </Box>
            <Box sx={{ minWidth: '200px' }}>
              <Typography variant="h3" component="div" color="primary.main" fontWeight={700}>
                1000+
              </Typography>
              <Typography variant="h6" color="text.secondary">
                Happy Companies
              </Typography>
            </Box>
          </Box>
        </Container>
      </Paper>
    </Box>
  );
};

export default Home;