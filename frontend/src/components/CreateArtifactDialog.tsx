import React, { useState } from 'react'
import { Dialog, DialogTitle, DialogContent, DialogActions, Button, TextField, MenuItem } from '@mui/material'
import type { ArtifactType } from '../api/types'

interface Props { open:boolean; onClose:()=>void; onCreate:(type:ArtifactType,url:string)=>Promise<void> }

export default function CreateArtifactDialog({open,onClose,onCreate}:Props){
  const [type,setType] = useState<ArtifactType>('model')
  const [url,setUrl] = useState('')
  const [loading,setLoading] = useState(false)

  const submit = async ()=>{
    setLoading(true)
    try{
      await onCreate(type,url)
      setUrl('')
      onClose()
    }finally{setLoading(false)}
  }

  return (
    <Dialog open={open} onClose={onClose}>
      <DialogTitle>Create Artifact</DialogTitle>
      <DialogContent>
        <TextField select margin="normal" label="Type" value={type} onChange={(e)=>setType(e.target.value as ArtifactType)} fullWidth>
          <MenuItem value="model">model</MenuItem>
          <MenuItem value="dataset">dataset</MenuItem>
          <MenuItem value="code">code</MenuItem>
        </TextField>
        <TextField margin="normal" label="URL" helperText="HTTP URL to create artifact from" value={url} onChange={(e)=>setUrl(e.target.value)} fullWidth />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={submit} disabled={!url || loading}>Create</Button>
      </DialogActions>
    </Dialog>
  )
}
