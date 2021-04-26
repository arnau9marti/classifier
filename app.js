const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs')
const app = express();
var path = require('path');

const livereload = require("livereload");

const liveReloadServer = livereload.createServer();
liveReloadServer.watch(path.join(__dirname, 'public'));

const connectLivereload = require("connect-livereload");

app.use(connectLivereload());
app.use(bodyParser.urlencoded({ extended: true })); 
app.use(express.static(__dirname));
app.set('view engine', 'pug')

var categories;

function classify(desc, mode, res) {
    // standard node module
    var exec = require('child_process').exec

    // this launches the executable and returns immediately
    var child = exec('sh script.sh',
    function (error, stdout, stderr) {
        // This callback is invoked once the child terminates
        console.log("Here is the complete output of the program: ");
        //console.log(error)
        console.log(stdout)
        //console.log(stderr)
        categories = stdout;

        fs.readFile('file.txt', 'utf-8', (err, data) => {
            if (err) throw err;
            console.log(data);
        })
        res.render('input', { name: "HOLA" }, function (err, html) {
            //const myVersion = 'My version is 0.5';
            //res.json(myVersion)
            res.sendFile(path.join(__dirname, 'result.html'));
        })
    
        //liveReloadServer.refresh('/');
    });

    // if the program needs input on stdin, you can write to it immediately
    //child.stdin.setEncoding('utf-8');
    //child.stdin.write(mode+"\n");
}

function delfile() {
    const { exec } = require("child_process");

exec("rm res.xml", (error, stdout, stderr) => {
    if (error) {
        console.log(`error: ${error.message}`);
        return;
    }
    if (stderr) {
        console.log(`stderr: ${stderr}`);
        return;
    }
    console.log(`stdout: ${stdout}`);
});
}

function newtxt(desc) {
    const { exec } = require("child_process");

exec("echo '"+desc+ "' >file.txt", (error, stdout, stderr) => {
    if (error) {
        console.log(`error: ${error.message}`);
        return;
    }
    if (stderr) {
        console.log(`stderr: ${stderr}`);
        return;
    }
    console.log(`stdout: ${stdout}`);
});
}

var pos = ["0","3"]; //EXAMPLE TODO READ FROM TOKENS

app.get('/', function(req, res,) {


    //res.render(path.join(__dirname, 'index.html'), { name: 'description', positions: pos});
});

app.post('/input', (req, res) => {
    if (req.body.lname == "") mode = "1";
    else mode = "0";
    desc = req.body.fname;
    //delfile();
    //newtxt(desc);
    classify(desc, mode, res);
});

const port = 8080;

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});