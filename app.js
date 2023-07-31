// app.js

const express = require('express');
const multer = require('multer');
const { PythonShell } = require('python-shell');
const path = require('path');

const app = express();
const upload = multer({ dest: 'uploads/' }); // Directory to store uploaded files

app.use(express.static('public')); // Serve static files from the 'public' directory

// Define a route for the root URL ("/") to serve the index.html file
app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'index.html'));
});


app.post('/upload', upload.single('file'), (req, res) => {
  const zipFilePath = req.file.path; // Path of the uploaded file
  const jobDescription = req.body.description; // Job description from the textarea

  const options = {
    pythonPath: 'python', // Change this to the path of your Python3 executable if needed
    args: [zipFilePath, jobDescription],
  };


  // Use PythonShell.run with Promise
  PythonShell.run('resume_parser.py', options)
    .then(results => {
      // Parse the output from the Python script and send it back as JSON
      console.log("Data is: "+results);
      const parsedResults = JSON.parse(results);
      res.json(parsedResults);
    })
    .catch(err => {
      console.error('Error executing Python script:', err);
      res.status(500).send('Error processing the file.');
    });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
