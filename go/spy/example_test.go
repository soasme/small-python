package spy_test

import (
	"fmt"
	"os"
	"strings"

	"github.com/soasme/small-python/go/spy"
)

func Example() {
	rt, err := spy.New()
	if err != nil {
		panic(err)
	}
	defer rt.Close()
	rt.Define("add", func(rt *spy.Runtime, args spy.Args) (any, error) {
		var a, b int
		if err := args.Scan(&a, &b); err != nil {
			return nil, err
		}
		return a + b, nil
	})
	n, err := spy.As[int](rt.Eval("add(40, 2)"))
	fmt.Println(n, err)
	// Output: 42 <nil>
}

func ExampleValue_Decode() {
	type User struct {
		Name  string   `spy:"name"`
		Roles []string `spy:"roles"`
		Admin bool     `spy:"-"`
	}
	rt, _ := spy.New()
	defer rt.Close()
	rt.Set("user", User{Name: "ada", Roles: []string{"dev"}})
	v, _ := rt.Eval("user | {'name': user['name'].title(), 'roles': user['roles'] + ['ops']}")
	var u User
	err := v.Decode(&u)
	fmt.Printf("%+v %v\n", u, err)
	// Output: {Name:Ada Roles:[dev ops] Admin:false} <nil>
}

func ExampleArgs() {
	rt, _ := spy.New()
	defer rt.Close()
	rt.Define("greet", func(rt *spy.Runtime, args spy.Args) (any, error) {
		var name string
		if err := args.Scan(&name); err != nil {
			return nil, err
		}
		end := "!"
		if v := args.Keywords["end"]; v != nil {
			if err := v.Decode(&end); err != nil {
				return nil, err
			}
		}
		return "hello " + name + end, nil
	})
	s, _ := spy.As[string](rt.Eval("greet('spy', end='?')"))
	fmt.Println(s)
	_, err := rt.Eval("greet()")
	fmt.Println(err)
	// Output:
	// hello spy?
	// TypeError: expected 1 argument, got 0
}

func ExampleRuntime_RegisterModule() {
	rt, _ := spy.New()
	defer rt.Close()
	rt.RegisterModule("config", func(rt *spy.Runtime, module *spy.Value) error {
		if err := module.SetAttr("region", "eu"); err != nil {
			return err
		}
		return rt.ExecModule(module, "def describe(): return 'region ' + region", "<config>")
	})
	rt.SetLoader(func(name string) (string, bool) {
		if name == "shapes" {
			return "def area(w, h): return w * h\n", true
		}
		return "", false
	})
	var out strings.Builder
	rt.SetOutput(&out)
	err := rt.Exec("import config, shapes\nprint(config.describe(), shapes.area(3, 4))")
	fmt.Print(out.String(), err)
	// Output: region eu 12
	// <nil>
}

func ExampleException() {
	rt, _ := spy.New()
	defer rt.Close()
	err := rt.Exec("x = 1\nraise ValueError('bad input')")
	if e, ok := err.(*spy.Exception); ok {
		fmt.Println(e.Type, e.Message, e.Line)
	}
	rt.Define("lookup", func(*spy.Runtime, spy.Args) (any, error) {
		return nil, spy.Raise("KeyError", "missing")
	})
	err = rt.Exec("try:\n    lookup()\nexcept KeyError as e:\n    print('caught', repr(e))")
	fmt.Println(err)
	// Output:
	// ValueError bad input 2
	// caught KeyError('missing')
	// <nil>
}

func ExampleValue_Iter() {
	rt, _ := spy.New()
	defer rt.Close()
	squares, _ := rt.Eval("(n * n for n in range(4))")
	for v, err := range squares.Iter() {
		n, err := spy.As[int](v, err)
		if err != nil {
			panic(err)
		}
		fmt.Print(n, " ")
	}
	fmt.Println()
	// Output: 0 1 4 9
}

func ExampleRuntime_Mount() {
	dir, _ := os.MkdirTemp("", "spy")
	defer os.RemoveAll(dir)
	os.WriteFile(dir+"/notes.txt", []byte("hello from the host\n"), 0o644)
	rt, _ := spy.New()
	defer rt.Close()
	rt.Mount(dir, "/data", true)
	s, _ := spy.As[string](rt.Eval("open('/data/notes.txt').read().strip()"))
	fmt.Println(s)
	_, err := rt.Eval("open('/data/new.txt', 'w')")
	fmt.Println(err.(*spy.Exception).Type)
	// Output:
	// hello from the host
	// OSError
}
