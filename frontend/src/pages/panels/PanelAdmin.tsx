import React, { useEffect, useState } from 'react'
import { Box, Paper, Button, Typography } from '@mui/material'
import { tracks, resetAll } from '../../api/registry'

export default function PanelAdmin(){
  const [tks,setTks] = useState<string[]>([])

  const load = async ()=> setTks((await tracks()).plannedTracks || [])

  useEffect(()=>{load()},[])

  const doReset = async ()=>{
    await resetAll()
    await load()
  }

  return (
    <Box>
      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Planned Tracks</Typography>
        {tks.map(t=> <Typography key={t}>{t}</Typography>)}
        <Button onClick={doReset} disabled={!localStorage.getItem('token')}>Reset Registry</Button>
      </Paper>
    </Box>
  )
}
