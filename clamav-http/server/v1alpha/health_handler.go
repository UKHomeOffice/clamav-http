package v1alpha

import (
	"net/http"
	"strings"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

const eicar = "X5O!P%@AP[4\\PZX54(P^)7CC)7}$EICAR-STANDARD-ANTIVIRUS-TEST-FILE!$H+H*"

const (
	healthError0 = iota
	healthError1 = iota
)

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
		hh.Logger.Errorf("healthcheck error %d: %s", healthError0, err.Error())
		return
	}

	result := <-response
	if result.Status == "FOUND" {
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("healthcheck: OK\n"))
		hh.Logger.Trace("healthcheck: OK")
	} else {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte("healthcheck: ERROR\n"))
		hh.Logger.Errorf("healthcheck error %d: %s", healthError1, err.Error())
	}
}
