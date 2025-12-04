import React from 'react'
import { Tabs, Tab, Paper } from '@mui/material'

interface Props { value: number; onChange: (v:number)=>void }

export default function TabsBar({value,onChange}:Props){
  return (
    <Paper sx={{borderRadius: 999, p:1, mb:2}} elevation={2}>
      <Tabs value={value} onChange={(_,v)=>onChange(v)} centered variant="fullWidth" aria-label="Main tabs">
        <Tab label="Artifacts" />
        <Tab label="Search" />
        <Tab label="Analysis" />
        <Tab label="Admin" />
        <Tab label="Health" />
      </Tabs>
    </Paper>
  )
}
