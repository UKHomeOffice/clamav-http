package v1alpha

import (
	"net/http"

	"github.com/dutchcoders/go-clamd"
	"github.com/sirupsen/logrus"
)

type ScanHandler struct {
	Address      string
	Max_file_mem int64
	Logger       *logrus.Logger
}

const (
	scan_error_0 = iota
	scan_error_1 = iota
	scan_error_2 = iota
)

func (sh *ScanHandler) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	err := r.ParseMultipartForm(sh.Max_file_mem * 1024 * 1024)

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		sh.Logger.Errorf("scan error %d: %s", scan_error_0, err.Error())
		return
	}

	files := r.MultipartForm.File["file"]

	if len(files) == 0 {
		w.WriteHeader(http.StatusNoContent)
		w.Write([]byte("empty file\n"))
		return
	}

	f, err := files[0].Open()
	defer f.Close()

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		sh.Logger.Errorf("scan error %d: %s", scan_error_1, err.Error())
		return
	}

	c := clamd.NewClamd(sh.Address)
	response, err := c.ScanStream(f, make(chan bool))

	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		w.Write([]byte(err.Error()))
		sh.Logger.Errorf("scan error %d: %s", scan_error_2, err.Error())
		return
	}

	result := <-response

	if result.Status == "OK" {
		w.WriteHeader(http.StatusOK)
		sh.Logger.Infof("Scanning %v: RES_OK", files[0].Filename)
		w.Write([]byte("AV Response : OK\n"))
	} else if result.Status == "FOUND" {
		w.WriteHeader(http.StatusForbidden)
		sh.Logger.Infof("Scanning %v: RES_FOUND", files[0].Filename)
		w.Write([]byte("AV Response : FOUND\n"))
	} else if result.Status == "ERROR" {
		w.WriteHeader(http.StatusBadRequest)
		sh.Logger.Infof("Scanning %v: RES_ERROR", files[0].Filename)
		w.Write([]byte("AV Response : ERROR\n"))
	} else if result.Status == "PARSE_ERROR" {
		w.WriteHeader(http.StatusPreconditionFailed)
		sh.Logger.Infof("Scanning %v: RES_PARSE_ERROR", files[0].Filename)
		w.Write([]byte("AV Response : PARSE_ERROR\n"))
	} else {
		w.WriteHeader(http.StatusNotImplemented)
	}
	return
}
