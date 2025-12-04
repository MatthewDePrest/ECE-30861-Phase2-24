import React, { useState } from 'react'
import { Box, Paper, TextField, Button, Switch, FormControlLabel, Snackbar, Alert } from '@mui/material'
import TabsBar from '../components/TabsBar'
import PanelArtifacts from './panels/PanelArtifacts'
import PanelSearch from './panels/PanelSearch'
import PanelAnalysis from './panels/PanelAnalysis'
import PanelAdmin from './panels/PanelAdmin'
import PanelHealth from './panels/PanelHealth'
import { authenticate } from '../api/registry'
import type { AuthenticationRequest } from '../api/types'

export default function Dashboard(){
  const [tab, setTab] = useState(0)
  const [name,setName] = useState('ece30861defaultadminuser')
  const [password,setPassword] = useState('')
  const [isAdmin,setIsAdmin] = useState(true)
  const [snack, setSnack] = useState<{open:boolean,msg:string,severity:'success'|'error'}>({open:false,msg:'',severity:'success'})

  const onAuth = async ()=>{
    const req: AuthenticationRequest = { user: { name, is_admin: isAdmin }, secret: { password } }
    try{
      await authenticate(req)
      setSnack({open:true,msg:'Authenticated',severity:'success'})
    }catch(e){
      setSnack({open:true,msg:'Authentication failed',severity:'error'})
    }
  }

  return (
    <Box>
      <Paper sx={{p:3, mb:2}}>
        <TextField label="Username" helperText="Enter username" value={name} onChange={(e)=>setName(e.target.value)} sx={{mr:2}} />
        <TextField label="Password" helperText="Enter password" type="password" value={password} onChange={(e)=>setPassword(e.target.value)} sx={{mr:2}} />
        <FormControlLabel control={<Switch checked={isAdmin} onChange={(e)=>setIsAdmin(e.target.checked)} />} label="Admin User" />
        <Button onClick={onAuth} sx={{ml:2}}>Authenticate</Button>
      </Paper>

      <TabsBar value={tab} onChange={setTab} />

      {tab===0 && <PanelArtifacts />}
      {tab===1 && <PanelSearch />}
      {tab===2 && <PanelAnalysis />}
      {tab===3 && <PanelAdmin />}
      {tab===4 && <PanelHealth />}

      <Snackbar open={snack.open} autoHideDuration={3000} onClose={()=>setSnack(s=>({...s,open:false}))}>
        <Alert severity={snack.severity}>{snack.msg}</Alert>
      </Snackbar>
    </Box>
  )
}
