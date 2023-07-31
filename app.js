// app.js

// const { PythonShell } = require('python-shell');

// const zipFilePath = './content/marketing_resumes.zip';
// const jobDescription = `We are seeking a talented and experienced Marketing Manager to join our team. As a Marketing Manager, you will be responsible for developing and implementing strategic marketing plans to drive brand awareness, enhance customer engagement, and generate leads. You will work closely with cross-functional teams to execute marketing campaigns and initiatives that align with our business objectives. Develop and execute comprehensive marketing strategies to promote our products/services and increase market share. Conduct market research to identify customer needs, market trends, and competitive landscape. Plan and implement digital marketing campaigns across various platforms, including social media, email marketing, content marketing, and search engine optimization (SEO). Monitor and analyze campaign performance, using data-driven insights to optimize marketing activities and achieve KPIs. Collaborate with the creative team to develop compelling marketing materials, including website content, blog posts, videos, and infographics. Build and maintain strong relationships with key stakeholders, such as media partners, industry influencers, and customers. Manage the marketing budget effectively, allocating resources to maximize ROI and achieve marketing goals. Stay updated on emerging marketing trends, technologies, and best practices to drive innovation and maintain a competitive edge. Lead and mentor a team of marketing professionals, providing guidance, support, and performance feedback. Bachelor's degree in Marketing, Business Administration, or a related field. MBA is a plus. Proven experience in marketing, with a focus on developing and implementing successful marketing strategies. Strong understanding of digital marketing channels, including social media, SEO, content marketing, and email marketing. Experience in analyzing marketing data and using metrics to drive decision-making and campaign optimization. Excellent written and verbal communication skills, with the ability to create engaging content and present ideas effectively. Strong project management skills, with the ability to manage multiple priorities and deliver projects on time. Demonstrated leadership abilities, with experience in managing and developing a team. Creative thinker with a passion for marketing and a drive to stay updated on industry trends and best practices. Results-oriented mindset, with a focus on achieving measurable marketing objectives.`;

// const options = {
//   pythonPath: 'python', // Change this to the path of your Python3 executable if needed
//   args: [zipFilePath, jobDescription],
// };

// PythonShell.run('resume_parser.py', options, function (err, results) {
//   if (err) throw err;
//   console.log('Resume Parsing Results:');
//   console.log(results);
// });



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

  PythonShell.run('resume_parser.py', options, function (err, results) {
    if (err) {
      console.error('Error executing Python script:', err);
      res.status(500).send('Error processing the file.');
      return;
    }

    // Parse the output from the Python script and send it back as JSON
    const parsedResults = JSON.parse(results);
    res.json(parsedResults);
  });
});

const PORT = 3000;
app.listen(PORT, () => {
  console.log(`Server is running on http://localhost:${PORT}`);
});
