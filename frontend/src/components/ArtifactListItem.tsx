import React from 'react'
import { Box, Paper, Chip, Typography, IconButton } from '@mui/material'
import OpenInNewIcon from '@mui/icons-material/OpenInNew'
import EditIcon from '@mui/icons-material/Edit'
import DeleteIcon from '@mui/icons-material/Delete'
import type { ArtifactMetadata } from '../api/types'

interface Props {
  metadata: ArtifactMetadata
  disabledActions?: boolean
  onOpen?: (m:ArtifactMetadata)=>void
  onEdit?: (m:ArtifactMetadata)=>void
  onDelete?: (m:ArtifactMetadata)=>void
}

const typeColor = (t:string)=> t==='model'? 'primary' : t==='dataset'? 'success' : 'info'

export default function ArtifactListItem({metadata, disabledActions, onOpen, onEdit, onDelete}:Props){
  return (
    <Paper sx={{display:'flex',alignItems:'center',p:2,my:1,borderRadius:4}} elevation={3} role="listitem">
      <Chip label={metadata.type} color={typeColor(metadata.type)} sx={{mr:2}} />
      <Box sx={{flex:1}}>
        <Typography fontWeight={700}>{metadata.name}</Typography>
        <Typography variant="caption">ID: {metadata.id}</Typography>
      </Box>
      <Box>
        <IconButton aria-label={`open-${metadata.id}`} onClick={()=>onOpen?.(metadata)}>
          <OpenInNewIcon />
        </IconButton>
        <IconButton aria-label={`edit-${metadata.id}`} disabled={disabledActions} onClick={()=>onEdit?.(metadata)}>
          <EditIcon />
        </IconButton>
        <IconButton aria-label={`delete-${metadata.id}`} disabled={disabledActions} onClick={()=>onDelete?.(metadata)}>
          <DeleteIcon />
        </IconButton>
      </Box>
    </Paper>
  )
}
