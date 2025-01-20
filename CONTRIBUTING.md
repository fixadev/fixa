# Contributing to fixa

We welcome contributions to the fixa framework! Your help makes this project better. Here's how to get started:

## Setting Up Your Development Environment

1. **Fork the Repository**

   - Click the "Fork" button in the top right
   - This creates your own copy of the repository

2. **Clone Your Fork**

   ```bash
   git clone https://github.com/your-username/fixa
   cd fixa
   ```

3. **Set Up Virtual Environment**

   ```bash
   # Create a virtual environment
   python -m venv venv

   # Activate the virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Unix or MacOS:
   source venv/bin/activate
   ```

4. **Install Development Dependencies**
   ```bash
   # Install the package in editable mode with development dependencies
   pip install -e .
   ```

## Making Contributions

1. **Create a New Branch**

   ```bash
   git checkout -b feature-or-fix-name
   ```

2. **Make Your Changes**

   - Write your code
   - Add tests if applicable
   - Update documentation as needed

3. **Test Your Changes**

   ```bash
   # Run tests (once test suite is set up)
   pytest
   ```

4. **Commit Your Changes**

   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

5. **Push to Your Fork**

   ```bash
   git push origin feature-or-fix-name
   ```

6. **Submit a Pull Request**
   - Go to your fork on GitHub
   - Click "New Pull Request"
   - Select your branch and submit
   - Provide a clear description of your changes
   - Link any related issues

## Need Help?

If you have questions or need help with the contribution process:

- Open an issue for general questions
- Tag maintainers in your PR for specific questions about your contribution

Thank you for contributing to fixa!
