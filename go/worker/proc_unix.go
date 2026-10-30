//go:build unix

package worker

import "syscall"

// The worker runs in its own process group, so a terminal's SIGINT reaches
// only the parent.
func sysProcAttr() *syscall.SysProcAttr {
	return &syscall.SysProcAttr{Setpgid: true}
}
