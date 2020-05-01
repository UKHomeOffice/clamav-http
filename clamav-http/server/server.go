package server

import (
	"fmt"
	"net"
	"net/http"

	"github.com/sirupsen/logrus"

	"github.com/ukhomeoffice/clamav-http/clamav-http/server/v0"
	"github.com/ukhomeoffice/clamav-http/clamav-http/server/v1alpha"
)

func RunHTTPListener(clamd_address string, port int, max_file_mem int64, logger *logrus.Logger) error {
	m := http.NewServeMux()
	hh := &v0.HealthHandler{
		Healthy: false,
		Logger:  logger,
	}
	m.Handle("/healthz", hh)
	m.Handle("/", &v0.PingHandler{
		Address: clamd_address,
		Logger:  logger,
	})
	m.Handle("/scan", &v0.ScanHandler{
		Address:      clamd_address,
		Max_file_mem: max_file_mem,
		Logger:       logger,
	})
	m.Handle("/scanReply", &v0.ScanReplyHandler{
		Address:      clamd_address,
		Max_file_mem: max_file_mem,
		Logger:       logger,
	})
	m.Handle("/v1alpha/healthz", &v1alpha.HealthHandler{
		Address: clamd_address,
		Logger:  logger,
	})
	m.Handle("/v1alpha/scan", &v1alpha.ScanHandler{
		Address:      clamd_address,
		Max_file_mem: max_file_mem,
		Logger:       logger,
	})
	logger.Infof("Starting the webserver on port %v", port)
	lis, err := net.Listen("tcp", fmt.Sprintf(":%d", port))
	if err != nil {
		return err
	}
	hh.Healthy = true
	return http.Serve(lis, m)
}
