const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs')
const path = require('path');
const app = express();

/*
const livereload = require("livereload");
const liveReloadServer = livereload.createServer();
liveReloadServer.watch(path.join(__dirname, 'public'));
const connectLivereload = require("connect-livereload");
app.use(connectLivereload());
*/

const exphbs = require('express-handlebars');
app.engine('handlebars', exphbs({
    defaultLayout: 'main',
    layoutsDir: path.join(__dirname, 'views/mainLayout')
}));

app.use(bodyParser.urlencoded({ extended: true })); 
app.use(express.static(__dirname));

app.set('view engine', 'handlebars');

var categories;
var description = "";

var pos = ["0","3"]; //EXAMPLE TODO READ FROM TOKENS

function classify(desc, mode, res) {
    var exec = require('child_process').exec

    var child = exec('sh script.sh',
    function (error, stdout, stderr) {
        console.log("Here is the complete output of the program: ");
        //console.log(error)
        console.log(stdout)
        //console.log(stderr)
        
        categories = stdout;
        pos = "machine";

        
        res.render('result', {text: description, position: pos});
    
        //liveReloadServer.refresh('/');
    });

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
app.get('/', (req, res) => {
    res.render('index', { name: "HOLA" });
});

app.post('/result', (req, res) => {
    if (req.body.lname == "") mode = "1";
    else mode = "0";
    desc = req.body.fname;
    //delfile();
    //newtxt(desc);
    fs.readFile('file.txt', 'utf-8', (err, data) => {
        if (err) throw err;
        description=data;
    })
    classify(desc, mode, res);
});

app.post('/modify', (req, res) => {
    console.log(req.body.word);

});

const port = 8080;

app.listen(port, () => {
  console.log(`Server running on port ${port}`);
});