import { combineReducers } from "redux";
// import inputValidation from "src/store/reducers/inputValidation";

const inputValidation = (state = "", action) => {
  switch (action.type) {
    case "SEND_VALUE":
      return action.payload;
    default:
      return state;
  }
};

export default combineReducers({ inputValidation });
