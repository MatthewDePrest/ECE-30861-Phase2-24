import React, { useState } from 'react'
import { Box, Paper, Button, Stack, Drawer, TextField, Typography } from '@mui/material'
import { listArtifacts, createArtifact, getArtifact, updateArtifact, deleteArtifact } from '../../api/registry'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import ArtifactListItem from '../../components/ArtifactListItem'
import CreateArtifactDialog from '../../components/CreateArtifactDialog'
import ConfirmDialog from '../../components/ConfirmDialog'
import type { ArtifactMetadata } from '../../api/types'

export default function PanelArtifacts(){
  const qc = useQueryClient()
  const [items,setItems] = useState<ArtifactMetadata[]>([])
  const [offset,setOffset] = useState<string|undefined>()
  const [openCreate,setOpenCreate] = useState(false)
  const [drawerContent,setDrawerContent] = useState<any>(null)
  const [confirm, setConfirm] = useState<{open:boolean,meta?:ArtifactMetadata}>({open:false})

  const fetchList = async (off?:string)=>{
    const r = await listArtifacts([{ name: '*' }], off)
    if (off) setItems(prev=>[...prev, ...r.items])
    else setItems(r.items)
    setOffset(r.nextOffset)
  }

  const handleCreate = async (type:string,url:string)=>{
    await createArtifact(type as any,{url})
    await fetchList()
  }

  const openDetails = async (m:ArtifactMetadata)=>{
    const r = await getArtifact(m.type, m.id)
    setDrawerContent(r)
  }

  const confirmDelete = async ()=>{
    if (!confirm.meta) return
    await deleteArtifact(confirm.meta.type, confirm.meta.id)
    setConfirm({open:false})
    await fetchList()
  }

  return (
    <Box>
      <Paper sx={{p:2,mb:2}}>
        <Stack direction="row" spacing={2}>
          <Button onClick={()=>fetchList()}>List Artifacts</Button>
          <Button onClick={()=>setOpenCreate(true)}>Create New</Button>
        </Stack>
      </Paper>

      <Paper sx={{p:2}} aria-live="polite">
        {items.length===0 && <Typography>No artifacts yet</Typography>}
        {items.map(it=> (
          <ArtifactListItem key={it.id} metadata={it} disabledActions={!localStorage.getItem('token')} onOpen={openDetails} onDelete={(m)=>setConfirm({open:true,meta:m})} />
        ))}
        {offset && <Button onClick={()=>fetchList(offset)}>Load more</Button>}
      </Paper>

      <CreateArtifactDialog open={openCreate} onClose={()=>setOpenCreate(false)} onCreate={handleCreate} />

      <Drawer anchor="right" open={!!drawerContent} onClose={()=>setDrawerContent(null)}>
        <Box sx={{width:420,p:2}}>
          <Typography variant="h6">Artifact details</Typography>
          <pre style={{whiteSpace:'pre-wrap'}}>{JSON.stringify(drawerContent, null, 2)}</pre>
        </Box>
      </Drawer>

      <ConfirmDialog open={confirm.open} title="Delete Artifact" onClose={()=>setConfirm({open:false})} onConfirm={confirmDelete}>
        Are you sure you want to delete {confirm.meta?.name}?
      </ConfirmDialog>
    </Box>
  )
}
