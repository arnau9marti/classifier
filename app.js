const express = require('express');
const bodyParser = require('body-parser');
const fs = require('fs')
const path = require('path');
const app = express();
const eol = require('eol')

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

function classify(res) {
    var exec = require('child_process').exec

    var child = exec('sh script.sh',
    function (error, stdout, stderr) {

        lines = eol.split(stdout)
        
        res.render('result', {text: description, res: res_name, out: lines});    
    });
}

function explore(res) {

    var exec = require('child_process').exec

    var child = exec('python3 knowledge.py 7',
    function (error, stdout, stderr) {

        lines = eol.split(stdout)
        
        res.render('index', {out: lines});    

    });

}

function execute (res,comm) {
    var exec = require('child_process').exec
    var child = exec(comm,
    function (error, stdout, stderr) {
        res.render('result', {text: description, res: res_name, out: lines});  
    });
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
    
    text=text.replace(/['"]+/g, '');

    exec('echo "'+text+'" >'+file_name, (error, stdout, stderr) => {
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
    explore(res);
});

app.get('/result', (req, res) => {
    res.render('result', {text: description, res: res_name, out: lines});  
});

app.post('/result', (req, res) => {
    if (req.body.lname == "" || req.body.fname == "") mode = "1";
    else mode = "0";
        
    if(mode == "0") res_name = req.body.lname;
    if(mode == "1") res_name = "SAMPLE NAME";
    
    newtxt("./classifier\npython3 knowledge.py 1 "+res_name, "script.sh");

    if(mode == "0") {
        description = req.body.fname;
        delfile("res.xml");
        newtxt(description, "file.txt");
    }

    if (mode == "1") {
        fs.readFile('file.txt', 'utf-8', (err, data) => {
            if (err) throw err;
            description = data;
        })
    }

    classify(res);
});

app.post('/modify', (req, res) => {
    mode = req.body.mode;

    // NEW TECH CATEGORY
    if (mode == "1") {
        cat_name = req.body.word;
        comm = "python3 knowledge.py 4 "+cat_name
        execute(res, comm)
    }
    // NEW BUSS CATEGORY
    if (mode == "2") {
        cat_name = req.body.word;
        comm = "python3 knowledge.py 3 "+cat_name
        execute(res, comm)
    }
    // ADD TOPIC RELATION
    if (mode == "3") {
        word = req.body.word;
        comm = "python3 knowledge.py 5 "+word
        execute(res, comm)
    }
    // NEW TOPIC
    if (mode == "4") {
        topic = req.body.topic;
        superTopic = req.body.superTopic;
        comm = "python3 knowledge.py 6 " + topic + " --------- " + superTopic
        execute(res, comm)
    }
    // END
    if (mode == "5") {
        buss_cat = req.body.buss_cat;
        tech_cat = req.body.tech_cat;
        newtxt("python3 knowledge.py 2 "+buss_cat+"\n" + "python3 knowledge.py 2 "+tech_cat+"\n" + "python3 knowledge.py 8", "end_script.sh");

        var exec2 = require('child_process').exec

        var child2 = exec2('sh end_script.sh',
        function (error, stdout, stderr) {
            console.log("REASONING MODULE UPDATED")
            res.render('result', {text: description, res: res_name, out: lines});  
        });
    }

});

const port = 8080;

app.listen(port, () => {
  //console.log(`Server running on port ${port}`);
});