package worker

import "syscall"

// The worker runs in its own process group, so Ctrl+C reaches only the
// parent.
func sysProcAttr() *syscall.SysProcAttr {
	return &syscall.SysProcAttr{CreationFlags: syscall.CREATE_NEW_PROCESS_GROUP}
}
