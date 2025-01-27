# Jest
	- Jest Basics:
		// Basic test structure
		it("test description", () => {
		  // test code here
		});
 
		// You can also use 'test' instead of 'it'
		test("test description", () => {
		  // test code here
		});
 
	- Common Jest Matchers:
		// Commonly used expectations
		expect(value).toBeInTheDocument();    // Check if element exists in DOM
		expect(value).not.toBeInTheDocument(); // Check if element doesn't exist
		expect(value).toHaveTextContent("text"); // Check text content
		expect(value).toHaveAttribute("attr", "value"); // Check attribute
 
	- Jest Mocks:
		// Mocking functions
		const mockFn = jest.fn();  // Create empty mock function
 
		// Spy on existing methods
		const alertMock = jest.spyOn(window, "alert").mockImplementation();
 
		// Verify mock calls
		expect(mockFn).toHaveBeenCalled();
		expect(mockFn).toHaveBeenCalledWith("argument");
 
	- Test Setup/Teardown:
		beforeEach(() => {
		  // Runs before each test
		});
 
		afterEach(() => {
		  // Runs after each test
		  cleanup();
		});
 
		beforeAll(() => {
		  // Runs once before all tests
		});
 
		afterAll(() => {
		  // Runs once after all tests
		});
 
	- Testing with React Testing Library:
		// Render component
		const { getByTestId, queryByTestId } = render(<Component />);
 
		// Fire events
		fireEvent.click(element);
		fireEvent.change(element, { target: { value: 'new value' }});
 
		// Query elements
		getByTestId('id');     // Throws if not found
		queryByTestId('id');   // Returns null if not found
 
 
	- Key Components Being Tested
		- Test Setup
			// Core imports
			import { render, fireEvent, cleanup } from "@testing-library/react";
			import "@testing-library/jest-dom/extend-expect";
 
			// Helper function to render App component
			const renderApp = () => render(<App />);
 
			// Cleanup after each test
			afterEach(() => cleanup());
 
		- Test Query Methods
			getByTestId: Finds element by data-testid, throws if not found
			queryByTestId: Similar to getByTestId but returns null if not found
 
		- Test Cases Overview
			- Initial Loading Test
				it("Test Initial Loading of the App", () => {
				  // Tests initial state of components
				  // Verifies dropdown content and disabled state
				  // Checks that certain elements are not present initially
				});
 
			- Alert Test
				it("Show alert on clicking show button...", () => {
				  // Tests validation when no patient is selected
				  // Uses jest.spyOn to mock window.alert
				});
 
			- Patient Details Test
				it("Test getting patient details", () => {
				  // Tests patient selection functionality
				  // Verifies correct display of patient data
				  // Checks medical records table content
				});
 
	- Key Testing Concepts Used
		- Component Queries
			const patientProfile = queryByTestId("patient-profile");
			const patientName = getByTestId("patient-name");
 
		- Event Simulation
			fireEvent.click(showBtn);
			fireEvent.change(patientName, { target: { value: "1" } });
 
		- Assertions
			expect(element).toBeInTheDocument();
			expect(element).toHaveTextContent("text");
			expect(mockFunction).toHaveBeenCalledWith("argument");
		- Mocking
			const alertMock = jest.spyOn(window, "alert").mockImplementation();
			global.console.error = jest.fn();
