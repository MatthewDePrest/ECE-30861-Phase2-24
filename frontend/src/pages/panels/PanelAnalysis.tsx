import React, { useState } from 'react'
import { Box, Paper, TextField, Button, Checkbox, FormControlLabel, Table, TableHead, TableRow, TableCell, TableBody, Typography } from '@mui/material'
import { modelRate, artifactCost, lineage, licenseCheck } from '../../api/registry'

export default function PanelAnalysis(){
  const [id,setId]=useState('')
  const [rating,setRating]=useState<any>(null)
  const [cost,setCost]=useState<any>(null)
  const [line,setLine]=useState<any>(null)
  const [dep,setDep]=useState(false)
  const [gh,setGh]=useState('')
  const [licenseRes,setLicenseRes]=useState<string|boolean>('')

  const doRate = async ()=> setRating(await modelRate(id))
  const doCost = async ()=> setCost(await artifactCost('model', id, dep))
  const doLine = async ()=> setLine(await lineage(id))
  const doLicense = async ()=> setLicenseRes(await licenseCheck(id, gh))

  return (
    <Box>
      <Paper sx={{p:2,mb:2}}>
        <TextField label="Artifact ID" value={id} onChange={(e)=>setId(e.target.value)} sx={{mr:2}} />
        <Button onClick={doRate}>Get Rating</Button>
        <FormControlLabel control={<Checkbox checked={dep} onChange={(e)=>setDep(e.target.checked)} />} label="dependency" />
        <Button onClick={doCost}>Get Cost</Button>
        <Button onClick={doLine}>Get Lineage</Button>
      </Paper>

      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Model Rating</Typography>
        {rating ? (
          <Table>
            <TableHead><TableRow><TableCell>Metric</TableCell><TableCell>Value</TableCell><TableCell>Latency</TableCell></TableRow></TableHead>
            <TableBody>
              {rating.metrics.map((m:any)=>(
                <TableRow key={m.metric}><TableCell>{m.metric}</TableCell><TableCell>{m.value}</TableCell><TableCell>{m.latencyMs||'-'}</TableCell></TableRow>
              ))}
            </TableBody>
          </Table>
        ):<Typography>No rating</Typography>}
      </Paper>

      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Cost</Typography>
        {cost ? <pre>{JSON.stringify(cost,null,2)}</pre> : <Typography>No cost</Typography>}
      </Paper>

      <Paper sx={{p:2,mb:2}}>
        <Typography variant="h6">Lineage</Typography>
        {line ? <pre>{JSON.stringify(line,null,2)}</pre> : <Typography>No lineage</Typography>}
      </Paper>

      <Paper sx={{p:2}}>
        <Typography variant="h6">License Check</Typography>
        <TextField label="Github URL" value={gh} onChange={(e)=>setGh(e.target.value)} sx={{mr:2}} />
        <Button onClick={doLicense}>Check</Button>
        <Typography aria-live="polite">Result: {String(licenseRes)}</Typography>
      </Paper>
    </Box>
  )
}
