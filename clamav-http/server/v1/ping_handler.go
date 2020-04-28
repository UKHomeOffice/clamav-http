package v1

import (
	"net/http"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

type PingHandler struct {
	Address string
	Logger  *logrus.Logger
}

func (ph *PingHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	c := clamd.NewClamd(ph.Address)
	err := c.Ping()
	if err != nil {
		ph.Logger.WithError(err).Infof("ping: not responding")
		w.WriteHeader(http.StatusOK)
		w.Write([]byte("Clamd responding: false\n"))
		return
	} else {
		w.WriteHeader(http.StatusOK)
		ph.Logger.Infof("ping: responding")
		w.Write([]byte("Clamd responding: true\n"))
		return
	}
}
