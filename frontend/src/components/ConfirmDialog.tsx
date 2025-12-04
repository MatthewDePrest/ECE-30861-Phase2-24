import React from 'react'
import { Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material'

interface Props { open:boolean; title?:string; children?:React.ReactNode; onClose:()=>void; onConfirm:()=>void }

export default function ConfirmDialog({open,title,children,onClose,onConfirm}:Props){
  return (
    <Dialog open={open} onClose={onClose} aria-labelledby="confirm-dialog">
      <DialogTitle id="confirm-dialog">{title || 'Confirm'}</DialogTitle>
      <DialogContent>{children}</DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button color="error" onClick={onConfirm}>Confirm</Button>
      </DialogActions>
    </Dialog>
  )
}
