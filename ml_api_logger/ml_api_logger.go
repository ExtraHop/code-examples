package main
import (
    "fmt"
    "io/ioutil"
    "net/http"
    "os"
)

func addyLog(w http.ResponseWriter, request *http.Request) {
    defer request.Body.Close()
    messageBytes, err := ioutil.ReadAll(request.Body)
    message := string(messageBytes[:])
    if err != nil {
        fmt.Printf("Error decoding response body: %s", err)
    }
    fmt.Println(message)
}

func main() {
    http.HandleFunc("/log", addyLog)
    err := http.ListenAndServeTLS(
        "localhost:" + os.Getenv("LOGGER_PORT"),
        os.Getenv("LOGGER_CERT"),
        os.Getenv("LOGGER_KEY"),
        nil,
    )
    if err != nil {
        fmt.Println(err)
    }
}
