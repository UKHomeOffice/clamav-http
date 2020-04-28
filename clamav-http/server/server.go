package server

import (
	"fmt"
	"net"
	"net/http"

	"github.com/sirupsen/logrus"

	"github.com/ukhomeoffice/clamav-http/clamav-http/server/v1"
	"github.com/ukhomeoffice/clamav-http/clamav-http/server/v2alpha"
)

func RunHTTPListener(clamd_address string, port int, max_file_mem int64, logger *logrus.Logger) error {
	m := http.NewServeMux()
	hh := &v1.HealthHandler{
		Healthy: false,
		Logger:  logger,
	}
	m.Handle("/healthz", hh)
	m.Handle("/", &v1.PingHandler{
		Address: clamd_address,
		Logger:  logger,
	})
	m.Handle("/scan", &v1.ScanHandler{
		Address:      clamd_address,
		Max_file_mem: max_file_mem,
		Logger:       logger,
	})
	m.Handle("/scanReply", &v1.ScanReplyHandler{
		Address:      clamd_address,
		Max_file_mem: max_file_mem,
		Logger:       logger,
	})
	m.Handle("/v2alpha/scan", &v2alpha.ScanHandler{
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
