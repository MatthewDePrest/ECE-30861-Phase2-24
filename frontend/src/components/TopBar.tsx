import React from 'react'
import { AppBar, Toolbar, Typography, Box } from '@mui/material'

export default function TopBar(){
  return (
    <AppBar position="static" color="transparent" elevation={0} sx={{backdropFilter:'blur(6px)'}}>
      <Toolbar>
        <Box sx={{flex:1}}>
          <Typography variant="h6">Trustworthy Model Registry</Typography>
          <Typography variant="caption">ECE 461 – Fall 2025 – Project Phase 2</Typography>
        </Box>
      </Toolbar>
    </AppBar>
  )
}
