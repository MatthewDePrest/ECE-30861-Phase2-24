import { createTheme } from '@mui/material'

export const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#1E4ED8' },
    background: {
      default: '#0B1020',
      paper: '#131A2A'
    }
  },
  shape: { borderRadius: 16 },
  components: {
    MuiCssBaseline: {
      styleOverrides: `
        *:focus-visible { outline: 2px solid #fff; outline-offset: 2px; }
      `
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          borderRadius: 16,
          boxShadow: '0 6px 18px rgba(2,6,23,0.6)'
        }
      }
    },
    MuiButton: {
      defaultProps: {
        variant: 'contained'
      },
      styleOverrides: {
        root: {
          borderRadius: 24
        }
      }
    }
  }
})
