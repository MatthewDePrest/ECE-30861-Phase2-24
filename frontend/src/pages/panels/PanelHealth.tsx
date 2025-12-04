import React, { useEffect, useState } from 'react'
import { Box, Paper, TextField, Button, Checkbox, FormControlLabel, Chip, Typography } from '@mui/material'
import { health, healthComponents } from '../../api/registry'

export default function PanelHealth(){
  const [raw,setRaw] = useState<any>(null)
  const [windowMinutes,setWindowMinutes] = useState(60)
  const [includeTimeline,setIncludeTimeline] = useState(false)
  const [components,setComponents] = useState<any[]>([])

  useEffect(()=>{ (async ()=> setRaw(await health()))() },[])

  const loadComponents = async ()=>{ const r = await healthComponents(windowMinutes, includeTimeline); setComponents(r.components || []) }

  const statusColor = (s:any)=> s==='ok'? 'success' : s==='degraded'? 'warning' : s==='critical'? 'error' : 'default'

  return (
    <Box>
      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Health</Typography>
        <pre aria-live="polite">{JSON.stringify(raw,null,2)}</pre>
      </Paper>

      <Paper sx={{p:2}}>
        <TextField type="number" label="Window Minutes" value={windowMinutes} onChange={(e)=>setWindowMinutes(Number(e.target.value))} inputProps={{min:5,max:1440}} sx={{mr:2}} />
        <FormControlLabel control={<Checkbox checked={includeTimeline} onChange={(e)=>setIncludeTimeline(e.target.checked)} />} label="Include Timeline" />
        <Button onClick={loadComponents}>Load Components</Button>
        <Box sx={{mt:2}} aria-live="polite">
          {components.map((c:any)=> (
            <Chip key={c.name} label={`${c.name}: ${c.status}`} color={statusColor(c.status)} sx={{mr:1,mb:1}} />
          ))}
        </Box>
      </Paper>
    </Box>
  )
}
