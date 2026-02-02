/**
 * Failed response messages displayed randomly when an error occurs
 */
export const FAILED_RESPONSES = [
  "I'm sorry, something went wrong. Please try again.",
  "Oops! I couldn't process your request. Please try again later.",
  "I'm having trouble understanding that. Could you please rephrase?",
  "Something unexpected happened. Please try again.",
  "I apologize, but I'm unable to help with that right now. Please try again.",
  "Sorry, I encountered an issue. Please try again in a moment.",
  "I'm currently experiencing difficulties. Please try again later.",
  "Oops! Something didn't work as expected. Please try again.",
  "I wasn't able to complete your request. Please try again.",
  "Sorry, something went wrong on my end. Please try again.",
  "I'm having a bit of trouble right now. Please try again shortly.",
  "Unable to process your request at this time. Please try again later.",
  "Apologies for the inconvenience. Please try again.",
  "I couldn't generate a response. Please try again.",
  "Something went wrong. Please rephrase your question and try again.",
  "I'm temporarily unavailable. Please try again in a few moments.",
  "Request failed. Please try again.",
  "Oops! Let's try that again.",
  "I hit a snag. Please try again.",
  "Sorry, I couldn't complete that. Give it another try!"
];

/**
 * Get a random error message
 * @returns {string} A random error message
 */
export const getRandomErrorMessage = () => {
  const randomIndex = Math.floor(Math.random() * FAILED_RESPONSES.length);
  return FAILED_RESPONSES[randomIndex];
};
