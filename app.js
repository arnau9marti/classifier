const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs')
const path = require('path');
const app = express();
const eol = require('eol')

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

var description = "";
var res_name = "";
var lines = "";

function classify(desc, mode, res) {
    var exec = require('child_process').exec

    var child = exec('sh script.sh',
    function (error, stdout, stderr) {
        topics = "machine";

        lines = eol.split(stdout)
        
        // lines.forEach(function(line) {
        //     console.log(line)
        // })
        
        res.render('result', {text: description, res: res_name, out: lines});    

    });
    //child.stdin.setEncoding('utf-8');
    //child.stdin.write(mode+"\n");
}

function delfile(file_name) {
    const { exec } = require("child_process");

    exec("rm "+file_name, (error, stdout, stderr) => {
        if (error) {
            console.log(`error: ${error.message}`);
            return;
        }
        if (stderr) {
            console.log(`stderr: ${stderr}`);
            return;
        }
        //console.log(`stdout: ${stdout}`);
    });
}

function newtxt(text, file_name) {
    const { exec } = require("child_process");

    exec("echo '"+text+ "' >"+file_name, (error, stdout, stderr) => {
        if (error) {
            console.log(`error: ${error.message}`);
            return;
        }
        if (stderr) {
            console.log(`stderr: ${stderr}`);
            return;
        }
        //console.log(`stdout: ${stdout}`);
    });
}

app.get('/', (req, res) => {
    res.render('index');
});
app.get('/result', (req, res) => {
    if (req.query.action == "Apply") {
        let superTopic = req.query.myTopic;
        console.log(superTopic)
    }
    res.render('result', {text: description, res: res_name, out: lines});

});

app.post('/result', (req, res) => {
    if (req.body.lname == "") mode = "1";
    else mode = "0";
    desc = req.body.fname;

    res_name = req.body.lname;
    res_name = "IOT LOGISTICS SYSTEM";
    
    newtxt("./classifier\npython3 knowledge.py 1 "+res_name, "script.sh");
    //newtxt("make\n./classifier\npython3 knowledge.py 1 "+res_name, "script.sh");

    //delfile("res.xml");
    //newtxt(desc, "file.txt");

    fs.readFile('file.txt', 'utf-8', (err, data) => {
        if (err) throw err;
        description=data;
    })
    classify(desc, mode, res);
});

app.post('/modify', (req, res) => {
    //console.log(req.body.word);

});

const port = 8080;

app.listen(port, () => {
  //console.log(`Server running on port ${port}`);
});