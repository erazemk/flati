package flatpak

import (
	"fmt"
	"os/exec"
	"strings"
)

// List returns a slice of all installed Flatpak packages, possibly filtered by their type (app or runtime)
func List(pkgType string) []Package {
	var params string

	if pkgType == "app" {
		params = "--app"
	} else if pkgType == "runtime" {
		params = "--runtime"
	} else { // Print all packages
	}

	var cmd *exec.Cmd
	if params == "" {
		cmd = exec.Command("flatpak", "list", "--columns=name,description,application,version,branch,arch,origin,installation,ref,size,options")
	} else {
		cmd = exec.Command("flatpak", "list", params, "--columns=name,description,application,version,branch,arch,origin,installation,ref,size,options")
	}

	output, err := cmd.Output()
	if err != nil {
		panic(err)
	}

	applications := strings.Split(string(output), "\n")
	if len(applications) == 0 {
		if debug {
			fmt.Println("No Flatpak packages installed")
			return nil
		}
	}

	applicationList := make([]Package, 0) // 0 is required to append properly

	// Split output by application and then by column
	for i, application := range applications[:len(applications)-1] { // -1 because the first line is the header

		if debug {
			fmt.Printf("Application (%d): %v\n", i, application)
		}

		columns := strings.Split(application, "\t")
		app := Package{
			name:         columns[0],
			description:  columns[1],
			id:           columns[2],
			version:      columns[3],
			branch:       columns[4],
			arch:         columns[5],
			origin:       columns[6],
			installation: columns[7],
			ref:          columns[8],
			size:         columns[9],
			options:      columns[10],
		}

		applicationList = append(applicationList, app)
	}

	return applicationList
}

// Search returns a slice of found packages matching the search term
func Search(pkgName string) []Package {
	cmd := exec.Command("flatpak", "search", "--columns=name,description,application,version,branch,remotes", pkgName)

	output, err := cmd.Output()
	if err != nil {
		panic(err)
	}

	if debug {
		fmt.Printf("[Flatpak output]: '%s'\n", string(output))
	}

	if strings.Contains(string(output), "No matches found") {
		if debug {
			fmt.Println("No packages found for search term " + pkgName)
		}

		return nil
	}

	applications := strings.Split(string(output), "\n")
	applicationList := make([]Package, 0) // 0 is required to append properly

	// Split output by application and then by column
	for i, application := range applications[:len(applications)-1] { // -1 because the first line is the header

		if debug {
			fmt.Printf("Application (%d): %v\n", i, application)
		}

		columns := strings.Split(application, "\t")
		app := Package{
			name:        columns[0],
			description: columns[1],
			id:          columns[2],
			version:     columns[3],
			branch:      columns[4],
			origin:      columns[5],
		}

		applicationList = append(applicationList, app)
	}

	return applicationList
}
