var http = require('http');
var redis = require('redis');
client = redis.createClient();

client.on("error", function(err){
    console.log("Error" + err);
});

var server = http.createServer(function(req, res){
    res.writeHead(200);
    res.end('Hello Http');
    client.set("string key", "string val", redis.print);
});

server.listen(8080);