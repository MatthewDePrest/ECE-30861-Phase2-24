import React, { useState } from 'react'
import { Box, Paper, TextField, Button, Typography } from '@mui/material'
import { byName, byRegex } from '../../api/registry'
import ArtifactListItem from '../../components/ArtifactListItem'

export default function PanelSearch(){
  const [name,setName]=useState('')
  const [regex,setRegex]=useState('')
  const [results,setResults]=useState<any[]>([])

  const doName = async ()=>{
    const r = await byName(name)
    setResults(r)
  }
  const doRegex = async ()=>{
    const r = await byRegex(regex)
    setResults(r)
  }

  return (
    <Box>
      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Search by Name</Typography>
        <TextField label="Name" value={name} onChange={(e)=>setName(e.target.value)} helperText="Exact name" sx={{mr:2}} />
        <Button onClick={doName}>Search</Button>
      </Paper>

      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Search by RegEx</Typography>
        <TextField label="RegEx" value={regex} onChange={(e)=>setRegex(e.target.value)} helperText="Regular expression" sx={{mr:2}} />
        <Button onClick={doRegex}>Search</Button>
      </Paper>

      <Paper sx={{p:2}} aria-live="polite">
        {results.map((r:any)=> <ArtifactListItem key={r.id} metadata={r} />)}
      </Paper>
    </Box>
  )
}
