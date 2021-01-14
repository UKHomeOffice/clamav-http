package v1alpha

import (
	"net/http"
	"strings"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

const eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

type HealthHandler struct {
	Address string
	Logger  *logrus.Logger
}

func (hh *HealthHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	c := clamd.NewClamd(hh.Address)
	response, err := c.ScanStream(strings.NewReader(eicar), make(chan bool))

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
	}

	result := <-response
	if result.Status == "FOUND" {
		w.WriteHeader(http.StatusOK)
		hh.Logger.Info("healthcheck: OK")
		w.Write([]byte("healthcheck: OK\n"))
	} else {
		w.WriteHeader(http.StatusInternalServerError)
		hh.Logger.Info("healthcheck: ERROR")
		w.Write([]byte("healthcheck: ERROR\n"))
	}

	return
}
