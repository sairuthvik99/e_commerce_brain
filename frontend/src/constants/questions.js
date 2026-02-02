/**
 * Predefined questions categorized by domain
 */
import AttachMoneyIcon from '@mui/icons-material/AttachMoney';
import InventoryIcon from '@mui/icons-material/Inventory';
import CampaignIcon from '@mui/icons-material/Campaign';
import HeadsetMicIcon from '@mui/icons-material/HeadsetMic';
import { createElement } from 'react';

// Icon components for categories
export const CATEGORY_ICONS = {
  sales: AttachMoneyIcon,
  inventory: InventoryIcon,
  marketing: CampaignIcon,
  support: HeadsetMicIcon
};

export const QUESTION_CATEGORIES = {
  sales: {
    title: "Sales & Revenue",
    icon: "sales",
    iconComponent: AttachMoneyIcon,
    description: "Analyze sales performance, revenue trends, and order metrics",
    questions: [
      "Why did sales drop yesterday?",
      "Compare yesterday's sales with last week.",
      "Which products contributed most to the revenue drop?",
      "Was the drop due to fewer orders or lower order value?",
      "Did any region perform worse than usual?",
      "Is this drop normal or an anomaly?",
      "Did sales recover today or is the trend continuing?"
    ]
  },
  inventory: {
    title: "Inventory & Supply",
    icon: "inventory",
    iconComponent: InventoryIcon,
    description: "Monitor stock levels, supply chain, and inventory health",
    questions: [
      "Were any top-selling products out of stock yesterday?",
      "Which products are close to stock-out?",
      "Did inventory issues impact conversions?",
      "Should we restock any product immediately?",
      "Which items were viewed but not purchased due to stock issues?"
    ]
  },
  marketing: {
    title: "Marketing & Campaigns",
    icon: "marketing",
    iconComponent: CampaignIcon,
    description: "Track campaign performance and marketing effectiveness",
    questions: [
      "Were any campaigns paused or underperforming?",
      "Did campaign performance drop compared to last week?",
      "Did we miss any scheduled promotions?",
      "Which channel performed the worst yesterday?",
      "Should we run a discount to recover sales?"
    ]
  },
  support: {
    title: "Customer Support",
    icon: "support",
    iconComponent: HeadsetMicIcon,
    description: "Monitor customer feedback, complaints, and support metrics",
    questions: [
      "Did customer complaints increase yesterday?",
      "Are refunds or returns higher than usual?",
      "Any negative reviews affecting conversions?",
      "Is there a common issue reported by customers?"
    ]
  }
};

/**
 * Get all questions as a flat array
 * @returns {Array} All questions
 */
export const getAllQuestions = () => {
  return Object.values(QUESTION_CATEGORIES).flatMap(category => category.questions);
};

/**
 * Get questions for a specific category
 * @param {string} categoryKey - The category key
 * @returns {Array} Questions for the category
 */
export const getQuestionsByCategory = (categoryKey) => {
  return QUESTION_CATEGORIES[categoryKey]?.questions || [];
};
