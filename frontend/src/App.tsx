import React from 'react'
import { Box, Container } from '@mui/material'
import TopBar from './components/TopBar'
import Dashboard from './pages/Dashboard'

export default function App(){
  return (
    <Box>
      <a className="skip-link" href="#main">Skip to main content</a>
      <TopBar />
      <Container maxWidth="lg" component="main" id="main" sx={{py:4}}>
        <Dashboard />
      </Container>
    </Box>
  )
}
